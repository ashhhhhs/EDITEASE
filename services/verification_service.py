"""Verification service: email verification tokens and email delivery."""
import secrets
import hashlib
import datetime
from bson import ObjectId
from pymongo import MongoClient

import config
from utils.logger import setup_logger
import resend

logger = setup_logger("verification_service")

RATE_LIMIT_PER_HOUR = 3

# Resend config
if config.RESEND_API_KEY:
    resend.api_key = config.RESEND_API_KEY

_client = None

def _get_db():
    global _client
    if _client is None:
        _client = MongoClient(config.MONGO_URI)
    return _client[config.DB_NAME]

def _hash_token(raw_token):
    return hashlib.sha256(raw_token.encode()).hexdigest()

def send_verification_email(email, raw_token):
    """Sends the verification email. Silently fails if no API key is set."""
    if not config.RESEND_API_KEY:
        logger.warning(f"No RESEND_API_KEY. Would have sent verification token {raw_token} to {email}")
        return

    # TODO: Once frontend router uses History API, this should be an absolute URL correctly resolving to frontend
    # Assuming frontend runs on same domain or we have an APP_BASE_URL
    app_url = config.APP_BASE_URL if hasattr(config, "APP_BASE_URL") else "http://localhost:5173"
    verify_url = f"{app_url}/verify-email/{raw_token}"

    html_content = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2>Verify your email address</h2>
        <p>Thanks for joining EDITEASE! Please verify your email address to unlock all features.</p>
        <div style="margin: 30px 0;">
            <a href="{verify_url}" style="background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Verify Email Address &rarr;</a>
        </div>
        <p style="color: #666; font-size: 14px;">This link expires in 24 hours.</p>
        <p style="color: #666; font-size: 14px;">If you didn't create an account, you can safely ignore this email.</p>
        <p style="color: #666; font-size: 14px; margin-top: 30px;">&ndash; The EDITEASE Team</p>
    </div>
    """


    try:
        if config.RESEND_API_KEY.startswith("re_"):
            # Only actually send if it looks like a real key to prevent crash on dummy key
            # In testing, we might want to bypass
            resend.Emails.send({
                "from": config.MAIL_FROM,
                "to": email,
                "subject": "Verify your EDITEASE email",
                "html": html_content
            })
            logger.info(f"Verification email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {e}")

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
