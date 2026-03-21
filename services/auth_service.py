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
