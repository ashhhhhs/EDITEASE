import os
from pymongo import MongoClient

import config
from utils.logger import setup_logger

logger = setup_logger("prepare_labels")

def prepare_training_labels():
    """
    Fetch reviewed clips from the database to prepare a training dataset label file.
    This runs offline for the AI calibrator when getting ready to train a new model.
    """
    client = MongoClient(config.MONGO_URI)
    db = client[config.DB_NAME]
    col = db[config.COLLECTION]
    
    reviewed_clips = list(col.find({"reviewed": True}))
    # Stub: format these into a JSON/CSV manifest and map to physical dataset folder
    logger.info(f"Found {len(reviewed_clips)} reviewed clips ready for ML training pipeline.")
    
    return reviewed_clips

if __name__ == "__main__":
    prepare_training_labels()
