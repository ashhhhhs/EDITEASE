import json
import os

from pymongo import ASCENDING, MongoClient

import config
from utils.logger import setup_logger

logger = setup_logger("ingest_to_mongo")


def _ensure_indexes(col):
    """Create the indexes needed by the review/search flows."""
    col.create_index([("_key", ASCENDING)], unique=True)
    col.create_index([("reviewed", ASCENDING)])
    col.create_index([("uncertain", ASCENDING)])
    col.create_index([("manual_scene_label", ASCENDING)])
    col.create_index([("video", ASCENDING)])
    col.create_index([("scene_label", ASCENDING)])
    col.create_index([("dominant_emotion_overall", ASCENDING)])
    col.create_index([("start_sec", ASCENDING)])
    col.create_index([("duration_sec", ASCENDING)])


def _prepare_scene_docs(data, source_name=None):
    prepared = []
    fallback_video = None
    if source_name:
        fallback_video = os.path.splitext(source_name)[0].replace("_scene_index", "")

    for original in data:
        if not isinstance(original, dict):
            continue

        doc = dict(original)
        if "video" not in doc and fallback_video:
            doc["video"] = fallback_video

        scene_id = doc.get("scene_id")
        video = doc.get("video")
        if not video or scene_id is None:
            continue

        doc["_key"] = f"{video}::{int(scene_id)}"
        prepared.append(doc)

    return prepared


def upsert_scene_docs(data,
                      source_name=None,
                      mongo_uri=config.MONGO_URI,
                      db_name=config.DB_NAME,
                      collection_name=config.COLLECTION):
    """Upsert a list of scene docs into MongoDB and return the number written."""
    if not isinstance(data, list):
        logger.warning("Skipping scene upsert because payload is not a list")
        return 0

    prepared = _prepare_scene_docs(data, source_name=source_name)
    if not prepared:
        logger.warning("No valid scene docs found to upsert from %s", source_name or "memory")
        return 0

    client = MongoClient(mongo_uri)
    col = client[db_name][collection_name]
    _ensure_indexes(col)

    upserts = 0
    for doc in prepared:
        col.update_one({"_key": doc["_key"]}, {"$set": doc}, upsert=True)
        upserts += 1

    logger.info("Upserted %s scenes into MongoDB from %s", upserts, source_name or "memory")
    return upserts


def ingest_scene_indexes(scene_indexes_dir="scene_indexes",
                         mongo_uri=config.MONGO_URI,
                         db_name=config.DB_NAME,
                         collection_name=config.COLLECTION):
    indexes_path = config.SCENE_INDEXES_DIR

    if not indexes_path.exists():
        print(f"Folder not found: {indexes_path}")
        return

    files = [f for f in os.listdir(indexes_path) if f.lower().endswith(".json")]
    if not files:
        print(f"No JSON files found in: {indexes_path}")
        return

    total_docs = 0

    for fname in files:
        fpath = indexes_path / fname
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            print(f"Skipping non-list file: {fname}")
            continue

        upserts = upsert_scene_docs(
            data,
            source_name=fname,
            mongo_uri=mongo_uri,
            db_name=db_name,
            collection_name=collection_name,
        )
        total_docs += upserts
        print(f"Ingested {upserts} scenes from {fname}")

    print(f"\nDONE. Total scenes upserted: {total_docs}")
    print(f"DB: {db_name}, Collection: {collection_name}")


if __name__ == "__main__":
    ingest_scene_indexes()
