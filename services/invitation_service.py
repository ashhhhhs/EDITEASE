"""Invitation service: generate, validate, and accept team invitations."""
import os
import secrets
import hashlib
import datetime
from pymongo import MongoClient
import config
from utils.logger import setup_logger

logger = setup_logger("invitation_service")

_client = None

def _get_invites_col():
    global _client
    if _client is None:
        _client = MongoClient(config.MONGO_URI)
    db = _client[config.DB_NAME]
    col = db["invitations"]
    try:
        col.create_index("token_hash", unique=True)
        col.create_index("email")
    except Exception as e:
        logger.error(f"Failed to verify invitations indexes: {e}")
    return col


def create_and_send_invitation(email, role, invited_by_id):
    """Generate a high-entropy invite token, store it, and send an email."""
    if role not in ["admin", "reviewer", "editor"]:
        return {"error": "Invalid role.", "status": 400}
        
    invites_col = _get_invites_col()
    
    # Check if a pending invite already exists (we could just overwrite/resend)
    # But for simplicity, we'll just create a new one each time.
    
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    now = datetime.datetime.utcnow()
    expires_at = now + datetime.timedelta(days=7) # Invites valid for 7 days
    
    invite_doc = {
        "email": email.lower(),
        "role": role,
        "invited_by": invited_by_id,
        "token_hash": token_hash,
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "accepted_at": None
    }
    
    invites_col.insert_one(invite_doc)

    # Send email via shared email_service (Flask-Mail)
    app_url = config.APP_BASE_URL
    invite_link = f"{app_url}/invite/{raw_token}"
    try:
        from services.email_service import send_invitation_email
        send_invitation_email(email, role, invite_link)
    except Exception as e:
        logger.error(f"Failed to send invitation email to {email}: {e}")
        # we don't return error here so the invite still registers internally

    return {"ok": True, "token": raw_token}  # API shouldn't return token unless testing


def validate_invitation(raw_token):
    """Check if an invite token is valid and return its details."""
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    invites_col = _get_invites_col()
    
    invite = invites_col.find_one({"token_hash": token_hash})
    if not invite:
        return {"error": "Invalid or expired invitation.", "status": 404}
        
    if invite.get("accepted_at"):
        return {"error": "This invitation has already been accepted.", "status": 400}
        
    now = datetime.datetime.utcnow().isoformat()
    if now > invite["expires_at"]:
        return {"error": "This invitation has expired.", "status": 400}
        
    return {
        "ok": True,
        "email": invite["email"],
        "role": invite["role"]
    }


def accept_invitation(raw_token, user_id, user_email):
    """Mark an invite as accepted and update the user's role and verification status."""
    from bson import ObjectId
    
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    invites_col = _get_invites_col()
    
    invite = invites_col.find_one({"token_hash": token_hash})
    if not invite:
        return {"error": "Invalid invitation.", "status": 400}
        
    if invite.get("accepted_at"):
        return {"error": "This invitation has already been accepted.", "status": 400}
        
    now = datetime.datetime.utcnow().isoformat()
    if now > invite["expires_at"]:
        return {"error": "This invitation has expired.", "status": 400}
        
    if invite["email"].lower() != user_email.lower():
        return {"error": f"This invitation was sent to {invite['email']}, but you are logged in as {user_email}.", "status": 400}
        
    # Mark accepted
    invites_col.update_one(
        {"_id": invite["_id"]},
        {"$set": {"accepted_at": now}}
    )
    
    # Update user
    db = _client[config.DB_NAME] # type: ignore
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "role": invite["role"],
            "email_verified": True # Accepting an invite verify their email implicitly
        }}
    )
    
    logger.info(f"User {user_id} accepted invite for role {invite['role']}")
    return {"ok": True, "role": invite["role"]}
