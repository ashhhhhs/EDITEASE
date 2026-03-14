import os
import json
from pymongo import MongoClient, ASCENDING, TEXT

import config

def ingest_scene_indexes(scene_indexes_dir="scene_indexes",
                        mongo_uri=config.MONGO_URI,
                        db_name=config.DB_NAME,
                        collection_name=config.COLLECTION):

    indexes_path = config.SCENE_INDEXES_DIR

    if not indexes_path.exists():
        print(f"❌ Folder not found: {indexes_path}")
        return

    client = MongoClient(mongo_uri)
    db = client[db_name]
    col = db[collection_name]

    # ✅ Create useful indexes (safe to run multiple times)
    col.create_index([("_key", ASCENDING)], unique=True)
    col.create_index([("reviewed", ASCENDING)])
    col.create_index([("uncertain", ASCENDING)])
    col.create_index([("manual_scene_label", ASCENDING)])

    col.create_index([("video", ASCENDING)])
    col.create_index([("scene_label", ASCENDING)])
    col.create_index([("dominant_emotion_overall", ASCENDING)])
    col.create_index([("start_sec", ASCENDING)])
    col.create_index([("duration_sec", ASCENDING)])

    # Optional: text search on labels/debug (can expand later)
    # col.create_index([("scene_label", TEXT)])

    files = [f for f in os.listdir(indexes_path) if f.lower().endswith(".json")]
    if not files:
        print(f"⚠️ No JSON files found in: {indexes_path}")
        return

    total_docs = 0

    for fname in files:
        fpath = indexes_path / fname
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            print(f"⚠️ Skipping (not a list): {fname}")
            continue

        # ✅ Avoid duplicates: build unique key = video + scene_id
        for d in data:
            if "video" not in d:
                # fallback if your older format didn’t store "video"
                d["video"] = os.path.splitext(fname)[0].replace("_scene_index", "")

            if "scene_id" not in d:
                continue

            d["_key"] = f"{d['video']}::{int(d['scene_id'])}"


        # Upsert each document (update if exists, insert if not)
        upserts = 0
        for d in data:
            if "_key" not in d:
                continue
            col.update_one({"_key": d["_key"]}, {"$set": d}, upsert=True)
            upserts += 1

        total_docs += upserts
        print(f"✅ Ingested {upserts} scenes from {fname}")

    print(f"\n🎉 DONE. Total scenes upserted: {total_docs}")
    print(f"DB: {db_name}, Collection: {collection_name}")

if __name__ == "__main__":
    ingest_scene_indexes()
