"""Auth service: user registration, login, token management, password reset."""
import secrets
import hashlib
import datetime
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

import config
from utils.logger import setup_logger

logger = setup_logger("auth_service")

_client = None
ACTIVE_ROLES = {"admin", "editor", "reviewer"}

def _normalize_email(email):
    return (email or "").strip().lower()

def _get_users_col():
    global _client
    if _client is None:
        _client = MongoClient(config.MONGO_URI)
    db = _client[config.DB_NAME]
    col = db["users"]
    try:
        col.create_index("email", unique=True)
        col.create_index("token")
        col.create_index("google_id", unique=True, sparse=True)
    except Exception as e:
        logger.error(f"Failed to verify users indexes: {e}")
    return col


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_user(email, password, name=None, confirm_password=None):
    """Create a new user account. Email is the primary identity key.

    Returns a dict with 'ok' on success or 'error' on failure.
    """
    email = _normalize_email(email)
    if not email or not password:
        return {"error": "Email and password are required.", "status": 400}

    if confirm_password is not None and password != confirm_password:
        return {"error": "Passwords do not match.", "status": 400}

    users_col = _get_users_col()
    if users_col.find_one({"email": email}):
        return {"error": "An account with this email already exists. Sign in or reset your password.", "status": 400}

    if len(password) < 8:
        return {"error": "Password must be at least 8 characters.", "status": 400}

    hashed = generate_password_hash(password)
    now = datetime.datetime.utcnow().isoformat()

    user = {
        "email": email,
        "password_hash": hashed,
        "name": name or email.split("@")[0],
        "token": None,
        "role": "editor",          # self-serve signup is always editor
        "email_verified": False,
        "is_active": True,
        "created_at": now,
        "last_login_at": None,
        "password_changed_at": None,
    }
    res = users_col.insert_one(user)
    user_id = str(res.inserted_id)
    logger.info(f"New user registered: {email}")

    # Trigger async verification email send
    from services.verification_service import create_and_send_verification
    try:
        create_and_send_verification(user_id, email)
    except Exception as e:
        logger.error(f"Failed to send initial verification email during registration: {e}")

    return {"ok": True, "user_id": user_id}


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def login_user(email, password):
    """Authenticate a user by email and password.

    Uses a single, non-enumerating error message for all credential failures
    to prevent account existence leakage.
    """
    email = _normalize_email(email)
    _CREDENTIAL_ERROR = {
        "error": "That email or password didn't match. Try again or reset your password.",
        "status": 401,
    }

    users_col = _get_users_col()
    user = users_col.find_one({"email": email})
    if not user:
        return _CREDENTIAL_ERROR

    pass_hash = user.get("password_hash")
    if not pass_hash or not check_password_hash(pass_hash, password):
        return _CREDENTIAL_ERROR

    if not user.get("is_active", True):
        return {"error": "This account has been deactivated. Contact support if you believe this is a mistake.", "status": 403}

    token = secrets.token_hex(32)
    now = datetime.datetime.utcnow().isoformat()
    users_col.update_one(
        {"_id": user["_id"]},
        {"$set": {"token": token, "last_login_at": now}}
    )

    _log_login_event(str(user["_id"]), "password")
    logger.info(f"User {str(user['_id'])} authenticated successfully with password.")

    return {
        "ok": True,
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role", "editor"),
            "email_verified": user.get("email_verified", False),
        },
    }


# ---------------------------------------------------------------------------
# Logout / Session
# ---------------------------------------------------------------------------

def logout_user(token):
    if not token:
        return {"error": "Token required.", "status": 400}
    users_col = _get_users_col()
    res = users_col.update_one({"token": token}, {"$set": {"token": None}})
    if res.modified_count == 0:
        return {"error": "Invalid token.", "status": 401}
    return {"ok": True}


def logout_all_sessions(user_id):
    """Invalidate all active sessions for a user (e.g. after password reset)."""
    from bson import ObjectId
    users_col = _get_users_col()
    users_col.update_one({"_id": ObjectId(user_id)}, {"$set": {"token": None}})


def get_user_by_token(token):
    if not token:
        return None
    users_col = _get_users_col()
    user = users_col.find_one({"token": token})
    if user and user.get("is_active", True):
        return {
            "id": str(user["_id"]),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role", "editor"),
            "email_verified": user.get("email_verified", False),
            "is_active": user.get("is_active", True),
            "created_at": user.get("created_at"),
            "last_login_at": user.get("last_login_at"),
        }
    return None


# ---------------------------------------------------------------------------
# Password Reset
# ---------------------------------------------------------------------------

def reset_password(user_id, new_password):
    """Update the user's password and invalidate all sessions.

    Called by the reset-password endpoint after the token is validated.
    """
    from bson import ObjectId

    if len(new_password) < 8:
        return {"error": "Password must be at least 8 characters.", "status": 400}

    hashed = generate_password_hash(new_password)
    now = datetime.datetime.utcnow().isoformat()

    users_col = _get_users_col()
    users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "password_hash": hashed,
            "password_changed_at": now,
            "token": None,          # invalidate all sessions immediately
        }}
    )
    logger.info(f"Password reset for user_id={user_id}")
    return {"ok": True}


# ---------------------------------------------------------------------------
# User Management (admin)
# ---------------------------------------------------------------------------

def get_paginated_users(page=1, limit=20, search='', role='', status='', sort='created_at', order='desc'):
    page = max(1, int(page))
    limit = max(1, min(int(limit), 200))
    skip = (page - 1) * limit
    users_col = _get_users_col()

    query = {}
    if search:
        query['$or'] = [
            {'username': {'$regex': search, '$options': 'i'}},
            {'email': {'$regex': search, '$options': 'i'}},
            {'name': {'$regex': search, '$options': 'i'}},
        ]
    if role and role != 'all':
        query['role'] = role
    if status == 'active':
        query['is_active'] = True
    elif status == 'inactive':
        query['is_active'] = False

    sort_order = -1 if order == 'desc' else 1
    cursor = (
        users_col
        .find(query, {"password_hash": 0, "token": 0})
        .sort(sort, sort_order)
        .skip(skip)
        .limit(limit)
    )
    users = []
    for u in cursor:
        u["_id"] = str(u["_id"])
        users.append(u)
    total = users_col.count_documents(query)
    return {"users": users, "total": total, "page": page, "limit": limit}


def get_user_summary_counts():
    """Return lightweight totals for admin dashboard cards."""
    users_col = _get_users_col()
    return {
        "total_users": users_col.count_documents({}),
        "active_users": users_col.count_documents({"is_active": True}),
    }


def _get_admin_count():
    users_col = _get_users_col()
    return users_col.count_documents({"role": "admin", "is_active": True})


def update_user_role(target_id, new_role, requester_id):
    from bson import ObjectId
    if new_role not in ACTIVE_ROLES:
        return {"error": "Invalid role.", "status": 400}
    if target_id == requester_id:
        return {"error": "Cannot change your own role.", "status": 403}
    try:
        target_obj_id = ObjectId(target_id)
    except Exception:
        return {"error": "Invalid user ID.", "status": 400}

    users_col = _get_users_col()
    user = users_col.find_one({"_id": target_obj_id})
    if not user:
        return {"error": "User not found.", "status": 404}

    if user.get("role") == "admin" and new_role != "admin":
        if _get_admin_count() <= 1:
            return {"error": "Cannot downgrade the last active admin.", "status": 403}

    users_col.update_one({"_id": target_obj_id}, {"$set": {"role": new_role}})
    return {"ok": True, "new_role": new_role}


def update_user_status(target_id, is_active, requester_id):
    from bson import ObjectId
    if target_id == requester_id:
        return {"error": "Cannot deactivate your own account.", "status": 403}
    try:
        target_obj_id = ObjectId(target_id)
    except Exception:
        return {"error": "Invalid user ID.", "status": 400}

    users_col = _get_users_col()
    user = users_col.find_one({"_id": target_obj_id})
    if not user:
        return {"error": "User not found.", "status": 404}

    if user.get("role") == "admin" and not is_active:
        if _get_admin_count() <= 1:
            return {"error": "Cannot deactivate the last active admin.", "status": 403}

    users_col.update_one({"_id": target_obj_id}, {"$set": {"is_active": is_active}})
    return {"ok": True, "is_active": is_active}

# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------

def login_with_google(id_token_str):
    """Verify Google token and authenticate/create user."""
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    import config
    
    if not config.GOOGLE_CLIENT_ID:
        return {"error": "Google sign-in is not configured.", "status": 500}
        
    try:
        request = google_requests.Request()
        id_info = id_token.verify_oauth2_token(
            id_token_str, request, config.GOOGLE_CLIENT_ID
        )
        
        email = id_info.get("email")
        google_id = id_info.get("sub")
        name = id_info.get("name")
        email = _normalize_email(email)
        
        if not email or not google_id:
            return {"error": "Incomplete profile from Google.", "status": 400}
            
        users_col = _get_users_col()
        user = users_col.find_one({"email": email})
        
        now = datetime.datetime.utcnow().isoformat()
        app_token = secrets.token_hex(32)
        
        if not user:
            # Create new user
            new_user = {
                "email": email,
                "password_hash": None,
                "name": name or email.split("@")[0],
                "token": app_token,
                "role": "editor",
                "email_verified": True, 
                "is_active": True,
                "created_at": now,
                "last_login_at": now,
                "password_changed_at": None,
                "google_id": google_id
            }
            res = users_col.insert_one(new_user)
            user_id = str(res.inserted_id)
            logger.info(f"New user registered via Google: {email}")
            _log_login_event(user_id, "google_signup")
            
            return {
                "ok": True,
                "token": app_token,
                "user": {
                    "id": user_id,
                    "name": new_user["name"],
                    "email": email,
                    "role": new_user["role"],
                    "email_verified": True
                }
            }
            
        else:
            if not user.get("is_active", True):
                return {"error": "This account has been deactivated.", "status": 403}
                
            if user.get("google_id") == google_id:
                # Normal login
                users_col.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"token": app_token, "last_login_at": now}}
                )
                _log_login_event(str(user["_id"]), "google_login")
                logger.info(f"User {str(user['_id'])} (Google: {google_id}) authenticated successfully")
                return {
                    "ok": True,
                    "token": app_token,
                    "user": {
                        "id": str(user["_id"]),
                        "name": user.get("name"),
                        "email": user.get("email"),
                        "role": user.get("role", "editor"),
                        "email_verified": user.get("email_verified", False)
                    }
                }
            else:
                # Email exists but not linked
                return {
                    "error": "This email belongs to an existing account. Sign in with your password to link your account.",
                    "code": "ACCOUNT_EXISTS_NEEDS_LINKING",
                    "status": 409,
                    "pending_link": {
                        "email": email,
                        "google_id": google_id
                    }
                }
                
    except ValueError as e:
        logger.error(f"Google token verification failed: {e}")
        return {"error": "Invalid Google token.", "status": 401}
    except Exception as e:
        logger.error(f"Error during Google sign-in: {e}", exc_info=True)
        return {"error": "An error occurred during Google sign in.", "status": 500}


def link_google_account(user_id, id_token_str):
    """Link a Google account to an existing user if the emails match."""
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    import config
    from bson import ObjectId
    
    if not config.GOOGLE_CLIENT_ID:
        return {"error": "Google sign-in is not configured.", "status": 500}
        
    try:
        request = google_requests.Request()
        id_info = id_token.verify_oauth2_token(
            id_token_str, request, config.GOOGLE_CLIENT_ID
        )
        
        email = id_info.get("email")
        google_id = id_info.get("sub")
        email = _normalize_email(email)
        
        users_col = _get_users_col()
        user = users_col.find_one({"_id": ObjectId(user_id)})
        
        if not user or user.get("email") != email:
            return {"error": "Google account email does not match your signed-in account email.", "status": 400}
            
        existing = users_col.find_one({"google_id": google_id})
        if existing and str(existing["_id"]) != str(user_id):
            return {"error": "This Google account is already linked to another user.", "status": 400}
            
        users_col.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"google_id": google_id, "email_verified": True}}
        )
        
        # Audit log for link
        _get_users_col().database["login_events"].insert_one({
            "user_id": ObjectId(user_id),
            "method": "google_link",
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
        
        logger.info(f"Google account linked to user {user_id}")
        return {"ok": True}
        
    except ValueError:
        return {"error": "Invalid Google token.", "status": 401}

# ---------------------------------------------------------------------------
# Account Settings
# ---------------------------------------------------------------------------

def _log_login_event(user_id, method):
    from bson import ObjectId
    try:
        col = _get_users_col().database["login_events"]
        col.insert_one({
            "user_id": ObjectId(user_id),
            "method": method,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Failed to log login event: {e}")

def update_user_password(user_id, current_password, new_password):
    from bson import ObjectId
    users_col = _get_users_col()
    user = users_col.find_one({"_id": ObjectId(user_id)})
    if not user:
        return {"error": "User not found.", "status": 404}
        
    if not user.get("password_hash"):
        return {"error": "You signed up with a linked provider (like Google). Please use the reset password flow to set a local password first.", "status": 400}
        
    if not check_password_hash(user["password_hash"], current_password):
        return {"error": "Incorrect current password.", "status": 403}
        
    if len(new_password) < 8:
        return {"error": "New password must be at least 8 characters.", "status": 400}
        
    hashed = generate_password_hash(new_password)
    now = datetime.datetime.utcnow().isoformat()
    new_token = secrets.token_hex(32)
    users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "password_hash": hashed,
            "password_changed_at": now,
            "token": new_token
        }}
    )
    return {"ok": True, "token": new_token}


def update_user_email(user_id, new_email):
    from bson import ObjectId
    users_col = _get_users_col()
    new_email = _normalize_email(new_email)
    
    existing = users_col.find_one({"email": new_email})
    if existing and str(existing["_id"]) != str(user_id):
        return {"error": "This email address is already in use by another account.", "status": 409}
        
    users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "email": new_email,
            "email_verified": False
        }}
    )
    
    try:
        from services.verification_service import create_and_send_verification
        create_and_send_verification(user_id, new_email)
    except Exception as e:
        logger.error(f"Failed to send verification for new email: {e}")
        
    return {"ok": True}


def sign_out_all_devices(user_id):
    """Force sign out all devices by setting token to a new one."""
    from bson import ObjectId
    users_col = _get_users_col()
    new_token = secrets.token_hex(32)
    users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"token": new_token}}
    )
    return {"ok": True, "token": new_token}
