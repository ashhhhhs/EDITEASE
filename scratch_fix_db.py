from pymongo import MongoClient
import config
db = MongoClient(config.MONGO_URI)[config.DB_NAME]
res = db.tasks.update_many(
    {"status": {"$in": ["PENDING", "STARTED"]}}, 
    {"$set": {"status": "FAILURE", "error_message": "Aborted due to worker restart", "progress_step": "error"}}
)
print(f"Fixed {res.modified_count} tasks.")
