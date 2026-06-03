import os
import json
from pymongo import MongoClient

import config

client = MongoClient(config.MONGO_URI)
db = client[config.DB_NAME]
col = db[config.COLLECTION]

def ingest_all():
    INDEX_DIR = config.SCENE_INDEXES_DIR
    if not INDEX_DIR.exists():
        print(f"❌ scene_indexes folder not found: {INDEX_DIR}")
        return

    files = [f for f in os.listdir(INDEX_DIR) if f.endswith("_scene_index.json")]
    print(f"📁 Found {len(files)} index files")

    total = 0
    for f in files:
        path = INDEX_DIR / f
        with open(path, "r", encoding="utf-8") as fp:
            scenes = json.load(fp)

        for s in scenes:
            video = s.get("video")
            scene_id = s.get("scene_id")
            if not video or scene_id is None:
                continue

            key = f"{video}::{int(scene_id)}"
            s["_key"] = key

            col.update_one({"_key": key}, {"$set": s}, upsert=True)
            total += 1

        print(f"✅ Ingested: {f} ({len(scenes)} scenes)")

    print(f"\n✅ Done. Upserted {total} scene docs into MongoDB.")
    print(f"DB={config.DB_NAME}, collection={config.COLLECTION}")

if __name__ == "__main__":
    ingest_all()
