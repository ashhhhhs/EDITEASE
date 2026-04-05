"""Verification service: email verification tokens and email delivery."""
import secrets
import hashlib
import datetime
from bson import ObjectId
from pymongo import MongoClient

import config
from utils.logger import setup_logger

logger = setup_logger("verification_service")

_client = None

def _get_db():
    global _client
    if _client is None:
        _client = MongoClient(config.MONGO_URI)
    return _client[config.DB_NAME]

def _hash_token(raw_token):
    return hashlib.sha256(raw_token.encode()).hexdigest()

RATE_LIMIT_PER_HOUR = 3

def send_verification_email(email, raw_token):
    """Send verification email via the shared email_service."""
    from services.email_service import send_verification_email as _send
    _send(email, raw_token)

def create_and_send_verification(user_id, email):
    """Generates a token, stores hash, and triggers email send."""
    db = _get_db()
    
    # 1. Generate secure random token
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    
    # 2. Expiry is typically longer for verification, e.g., 24 hours
    now = datetime.datetime.utcnow()
    expires_at = now + datetime.timedelta(hours=24)
    
    doc = {
        "user_id": ObjectId(user_id),
        "token_hash": token_hash,
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "used_at": None,
        "type": "email_verification"
    }
    
    # Optional: invalidate previous unused verification tokens for this user
    db.email_verification_tokens.update_many(
        {"user_id": ObjectId(user_id), "used_at": None},
        {"$set": {"used_at": now.isoformat(), "invalidated": True}}
    )
    
    db.email_verification_tokens.insert_one(doc)
    
    # 3. Send email async or inline
    send_verification_email(email, raw_token)

def verify_token(raw_token):
    """
    Validates token and marks as used.
    Returns:
      {"ok": True, "user_id": str} on success
      {"error": "message", "status": int} on failure
    """
    db = _get_db()
    token_hash = _hash_token(raw_token)
    
    token_doc = db.email_verification_tokens.find_one({"token_hash": token_hash})
    
    if not token_doc:
        return {"error": "Invalid or expired verification link.", "status": 400}
        
    if token_doc.get("used_at") is not None:
        # If it's invalidated (replaced) it shouldn't say "already verified", but "expired"
        if token_doc.get("invalidated"):
             return {"error": "Invalid or expired verification link.", "status": 400}
        return {"error": "This link has already been used.", "status": 400}
        
    now = datetime.datetime.utcnow()
    expires_at = datetime.datetime.fromisoformat(token_doc["expires_at"])
    
    if now > expires_at:
        return {"error": "Invalid or expired verification link.", "status": 400}
        
    # Mark as used
    db.email_verification_tokens.update_one(
        {"_id": token_doc["_id"]},
        {"$set": {"used_at": now.isoformat()}}
    )
    
    # Update user
    user_id = token_doc["user_id"]
    db.users.update_one(
        {"_id": user_id},
        {"$set": {"email_verified": True}}
    )
    
    return {"ok": True, "user_id": str(user_id)}

def resend_verification(user_id, email):
    """Rate-limited method to resend a verification email."""
    db = _get_db()
    one_hour_ago = (datetime.datetime.utcnow() - datetime.timedelta(hours=1)).isoformat()
    
    recent_count = db.email_verification_tokens.count_documents({
        "user_id": ObjectId(user_id),
        "created_at": {"$gte": one_hour_ago},
    })
    
    if recent_count >= RATE_LIMIT_PER_HOUR:
        logger.warning(f"Verification rate limit exceeded for user_id={user_id}")
        return {"error": "Too many verification requests. Please try again later.", "status": 429}
        
    create_and_send_verification(user_id, email)
    return {"ok": True}
