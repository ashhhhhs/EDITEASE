import secrets
import datetime
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

import config
from utils.logger import setup_logger

logger = setup_logger("auth_service")

client = MongoClient(config.MONGO_URI)
db = client[config.DB_NAME]
users_col = db["users"]

try:
    users_col.create_index("username", unique=True)
    users_col.create_index("email", unique=True)
    users_col.create_index("token")
except Exception as e:
    logger.error(f"Failed to verify users indexes: {e}")

def register_user(username, password, name=None, email=None):
    if not username or not password:
        return {"error": "Username and password required", "status": 400}
    
    if users_col.find_one({"username": username}):
        return {"error": "Username already exists", "status": 400}
        
    if email and users_col.find_one({"email": email}):
        return {"error": "Email already exists", "status": 400}
        
    hashed = generate_password_hash(password)
    now = datetime.datetime.utcnow().isoformat()
    
    user = {
        "username": username,
        "password_hash": hashed,
        "name": name or username,
        "email": email,
        "token": None,
        "role": "admin",
        "is_active": True,
        "created_at": now,
        "last_login_at": None
    }
    res = users_col.insert_one(user)
    return {"ok": True, "user_id": str(res.inserted_id), "username": username}

def login_user(username, password):
    user = users_col.find_one({"username": username})
    if not user:
        return {"error": "Invalid username or password", "status": 401}
        
    if not check_password_hash(user["password_hash"], password):
        return {"error": "Invalid username or password", "status": 401}
        
    if not user.get("is_active", True):
        return {"error": "Account is disabled", "status": 403}
        
    token = secrets.token_hex(32)
    now = datetime.datetime.utcnow().isoformat()
    users_col.update_one({"_id": user["_id"]}, {"$set": {"token": token, "last_login_at": now}})
    
    return {
        "ok": True, 
        "token": token, 
        "user": {
            "id": str(user["_id"]),
            "username": username,
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role", "admin")
        }
    }

def logout_user(token):
    if not token:
        return {"error": "Token required", "status": 400}
        
    res = users_col.update_one({"token": token}, {"$set": {"token": None}})
    if res.modified_count == 0:
        return {"error": "Invalid token", "status": 401}
    return {"ok": True}

def get_user_by_token(token):
    if not token:
        return None
    user = users_col.find_one({"token": token})
    if user and user.get("is_active", True):
        return {
            "id": str(user["_id"]),
            "username": user["username"],
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role", "admin"),
            "is_active": user.get("is_active", True),
            "created_at": user.get("created_at"),
            "last_login_at": user.get("last_login_at")
        }
    return None

def get_paginated_users(page=1, limit=20):
    page = max(1, int(page))
    limit = max(1, min(int(limit), 200))
    skip = (page - 1) * limit
    cursor = users_col.find({}, {"password_hash": 0, "token": 0}).sort("created_at", -1).skip(skip).limit(limit)
    users = []
    for u in cursor:
        u["_id"] = str(u["_id"])
        users.append(u)
    total = users_col.count_documents({})
    return {"users": users, "total": total, "page": page, "limit": limit}

def _get_admin_count():
    return users_col.count_documents({"role": "admin", "is_active": True})

def update_user_role(target_id, new_role, requester_id):
    from bson import ObjectId
    if target_id == requester_id:
        return {"error": "Cannot change your own role", "status": 403}
    
    try:
        target_obj_id = ObjectId(target_id)
    except:
        return {"error": "Invalid user ID", "status": 400}
        
    user = users_col.find_one({"_id": target_obj_id})
    if not user:
        return {"error": "User not found", "status": 404}
        
    if user.get("role") == "admin" and new_role != "admin":
        if _get_admin_count() <= 1:
            return {"error": "Cannot downgrade the last active admin", "status": 403}
            
    users_col.update_one({"_id": target_obj_id}, {"$set": {"role": new_role}})
    return {"ok": True, "new_role": new_role}

def update_user_status(target_id, is_active, requester_id):
    from bson import ObjectId
    if target_id == requester_id:
        return {"error": "Cannot deactivate your own account", "status": 403}
        
    try:
        target_obj_id = ObjectId(target_id)
    except:
        return {"error": "Invalid user ID", "status": 400}
        
    user = users_col.find_one({"_id": target_obj_id})
    if not user:
        return {"error": "User not found", "status": 404}
        
    if user.get("role") == "admin" and not is_active:
        if _get_admin_count() <= 1:
            return {"error": "Cannot deactivate the last active admin", "status": 403}
            
    users_col.update_one({"_id": target_obj_id}, {"$set": {"is_active": is_active}})
    return {"ok": True, "is_active": is_active}
