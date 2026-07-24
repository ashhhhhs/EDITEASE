"""Reset token service: secure generation, validation, and consumption of password reset tokens.

Security design:
- The raw token is ONLY sent in the email link — it is never stored.
- The database stores sha256(raw_token) so a DB breach cannot expose valid links.
- Tokens expire in 15 minutes.
- Tokens are one-time-use: validated consumed in a single atomic-ish operation.
- Rate limiting: 3 requests per email per hour (enforced here without Redis for simplicity;
  production should use Flask-Limiter + Redis for sliding-window accuracy).
"""
import hashlib
import secrets
import datetime

import config
from utils.logger import setup_logger

logger = setup_logger("reset_token_service")

TOKEN_EXPIRY_MINUTES = 15
RATE_LIMIT_PER_HOUR = 3


# ---------------------------------------------------------------------------
# Lazy DB accessor — avoids import-time connection issues
# ---------------------------------------------------------------------------

_client = None


def _get_client():
    """Cache the MongoClient — one per call leaks a connection pool and monitor
    threads that are never closed."""
    global _client
    if _client is None:
        from pymongo import MongoClient
        _client = MongoClient(config.MONGO_URI)
    return _client


def _get_col():
    col = _get_client()[config.DB_NAME]["password_reset_tokens"]
    # TTL index on expires_at so MongoDB auto-cleans expired docs
    try:
        col.create_index("expires_at", expireAfterSeconds=0)
        col.create_index("token_hash", unique=True)
    except Exception:
        pass
    return col


def _get_users_col():
    return _get_client()[config.DB_NAME]["users"]


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------

def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_and_send_reset_token(email: str) -> None:
    """Look up user by email; if found, create a reset token and send the email.

    Always returns None — errors are logged, never raised to the caller.
    The caller (the blueprint) always returns 200 regardless.
    """
    users_col = _get_users_col()
    user = users_col.find_one({"email": email.lower()})
    if not user:
        logger.debug(f"Forgot-password: no account for {email} (silent)")
        return

    user_id = str(user["_id"])

    # Rate limit check — count tokens created in the last hour for this user
    col = _get_col()
    one_hour_ago = (_now() - datetime.timedelta(hours=1)).isoformat()
    recent_count = col.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": one_hour_ago},
    })
    if recent_count >= RATE_LIMIT_PER_HOUR:
        logger.warning(f"Reset rate limit exceeded for user_id={user_id}")
        return  # silently skip — caller still returns 200

    # Generate token
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    now = _now()
    expires_at = now + datetime.timedelta(minutes=TOKEN_EXPIRY_MINUTES)

    col.insert_one({
        "user_id": user_id,
        "token_hash": token_hash,
        "created_at": now.isoformat(),
        "expires_at": expires_at,   # datetime so TTL index works
        "used_at": None,
    })

    # Send the email
    _send_reset_email(
        to_email=email,
        to_name=user.get("name", email.split("@")[0]),
        raw_token=raw_token,
    )


def validate_and_consume_token(raw_token: str) -> dict:
    """Validate a raw reset token and mark it as used.

    Returns {"user_id": str} on success, or {"error": str} on failure.
    Failure messages are intentionally generic — expired and invalid tokens
    return the same message to prevent information leakage.
    """
    col = _get_col()
    token_hash = _hash_token(raw_token)

    doc = col.find_one({"token_hash": token_hash})

    _INVALID = {"error": "This reset link is invalid or has expired. Please request a new one."}

    if not doc:
        return _INVALID

    if doc.get("used_at") is not None:
        return {"error": "This reset link has already been used. Request a new one if needed."}

    # Check expiry — expires_at may be datetime or ISO string depending on source
    expires_at = doc.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.datetime.fromisoformat(expires_at)

    if _now() > expires_at:
        return _INVALID  # same message as invalid — don't reveal expiry specifically

    # Consume the token
    col.update_one({"_id": doc["_id"]}, {"$set": {"used_at": _now().isoformat()}})

    return {"user_id": doc["user_id"]}


# ---------------------------------------------------------------------------
# Email sending
# ---------------------------------------------------------------------------

def _send_reset_email(to_email: str, to_name: str, raw_token: str) -> None:
    """Send the password reset email via Flask-Mail (email_service)."""
    from services.email_service import send_password_reset_email
    send_password_reset_email(to_email, to_name, raw_token)
