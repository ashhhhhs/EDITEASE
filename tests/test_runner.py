import os
import sys

# set pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pymongo import MongoClient
import config
from services import auth_service

def run():
    print("Testing auth service insertion...")
    original_db = config.DB_NAME
    config.DB_NAME = "editease_test_db"
    
    client = MongoClient(config.MONGO_URI)
    db = client[config.DB_NAME]
    
    # Fully drop the collection to nuke all indexes
    db.users.drop()
    db.password_reset_tokens.drop()
    print("Collections dropped")
    
    res = auth_service.register_user("testrunner@example.com", "StrongPassword123!", "Runner")
    print("Register result:", res)
    
    if "error" in res:
        print("FAILED TO INSERT")
    else:
        print("SUCCESS")
        
    config.DB_NAME = original_db

if __name__ == "__main__":
    run()
