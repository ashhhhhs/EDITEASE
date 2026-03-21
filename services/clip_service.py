import os
from bson import ObjectId
from pymongo import ASCENDING, MongoClient

import config
from utils.logger import setup_logger

logger = setup_logger("clip_service")

# Initialize MongoDB connection globally for the service
client = MongoClient(config.MONGO_URI)
db = client[config.DB_NAME]
col = db[config.COLLECTION]

# Ensure indexes if not already done via api_server previously
try:
    col.create_index([("scene_label", ASCENDING)])
    col.create_index([("reviewed", ASCENDING)])
    col.create_index([("video", ASCENDING)])
except Exception as e:
    logger.error(f"Failed to verify MongoDB indexes: {e}")

def clean_doc(d):
    """Convert Mongo _id to string so JSON can return it."""
    if not d:
        return d
    if "_id" in d:
        d["_id"] = str(d["_id"])
    return d

def face_present(doc):
    """
    Returns True if the scene has any detected face (new schema),
    or can be inferred from emotion_timeline (older schema).
    """
    faces = doc.get("faces") or {}
    if "face_present_any" in faces:
        return bool(faces["face_present_any"])

    # fallback inference from emotion_timeline for older docs
    tl = doc.get("emotion_timeline") or []
    for e in tl:
        if e.get("face_detected") is True:
            return True
        if e.get("emotion") is not None:
            return True
    return False

def search_clips(filters, limit=100):
    limit = max(1, min(int(limit), 200))
    q = {}

    scene_label = filters.get("scene_label")
    if scene_label:
        q["scene_label"] = scene_label

    emotion = filters.get("emotion")
    if emotion:
        if emotion == "__NULL__":
            q["$or"] = [
                {"dominant_emotion_overall": None},
                {"dominant_emotion_overall": {"$exists": False}}
            ]
        else:
            q["dominant_emotion_overall"] = emotion

    video = filters.get("video")
    if video:
        q["video"] = video

    reviewed = filters.get("reviewed")
    if reviewed is not None:
        if isinstance(reviewed, str):
            if reviewed.lower() in ("true", "false", "1", "0"):
                q["reviewed"] = reviewed.lower() in ("true", "1")
        elif isinstance(reviewed, bool):
            q["reviewed"] = reviewed

    uncertain = filters.get("uncertain")
    if uncertain is not None:
        if isinstance(uncertain, str):
            if uncertain.lower() in ("true", "false", "1", "0"):
                q["uncertain"] = uncertain.lower() in ("true", "1")
        elif isinstance(uncertain, bool):
            q["uncertain"] = uncertain

    min_duration = filters.get("min_duration")
    max_duration = filters.get("max_duration")
    if min_duration is not None or max_duration is not None:
        q["duration_sec"] = {}
        if min_duration is not None:
            q["duration_sec"]["$gte"] = float(min_duration)
        if max_duration is not None:
            q["duration_sec"]["$lte"] = float(max_duration)
            
    # Pagination
    page = max(1, int(filters.get("page", 1)))
    limit = max(1, min(int(limit), 200)) # Default max 200 via param
    skip = (page - 1) * limit

    total = col.count_documents(q)
    cursor = col.find(q).sort("duration_sec", -1).skip(skip).limit(limit)
    results = [clean_doc(d) for d in cursor]
    return {"count": len(results), "total": total, "page": page, "limit": limit, "query": q, "results": results}

def bulk_update_clips(keys, update_data):
    if not keys:
        return {"error": "no keys provided"}
        
    allowed = {
        "scene_label",
        "dominant_emotion_overall",
        "reviewed",
        "notes",
        "manual_scene_label",
        "manual_emotion",
        "uncertain",
    }
    
    update_fields = {}
    for k, v in update_data.items():
        if k in allowed:
            if k in ("reviewed", "uncertain") and not isinstance(v, bool):
                if isinstance(v, str):
                    update_fields[k] = v.lower() == "true"
                else:
                    return {"error": f"{k} must be boolean"}
            else:
                update_fields[k] = v
                
    if not update_fields:
        return {"error": "No valid fields provided to update."}
        
    res = col.update_many({"_key": {"$in": keys}}, {"$set": update_fields})
    return {"ok": True, "updated_count": res.modified_count, "fields": update_fields}

def update_clip(video, scene_id, data):
    if not video or scene_id is None:
        return {"error": "video and scene_id required"}
        
    try:
        scene_id = int(scene_id)
    except ValueError:
        return {"error": "invalid scene_id format"}

    key = f"{video}::{int(scene_id)}"
    doc = col.find_one({"_key": key})
    if not doc:
        return {"error": "scene not found", "key": key}

    has_face_any = face_present(doc)

    allowed = {
        "scene_label",
        "dominant_emotion_overall",
        "reviewed",
        "notes",
        "manual_scene_label",
        "manual_emotion",
        "uncertain",
    }

    update_fields = {}
    for k, v in data.items():
        if k in allowed:
            if k in ("reviewed", "uncertain") and not isinstance(v, bool):
                return {"error": f"{k} must be boolean"}
            update_fields[k] = v

    if not update_fields:
        return {"error": "No valid fields provided to update."}

    if "scene_label" in update_fields and "manual_scene_label" not in update_fields:
        update_fields["manual_scene_label"] = update_fields["scene_label"]

    if not has_face_any:
        if "dominant_emotion_overall" in update_fields:
            update_fields["dominant_emotion_overall"] = None
        if "manual_emotion" in update_fields:
            update_fields["manual_emotion"] = None

    res = col.update_one({"_key": key}, {"$set": update_fields})
    if res.matched_count == 0:
        return {"error": "scene not found", "key": key}

    doc2 = col.find_one({"_key": key})
    return {"ok": True, "updated": update_fields, "doc": clean_doc(doc2)}

def get_clip_by_id(clip_id):
    try:
        if isinstance(clip_id, str):
            clip_id = ObjectId(clip_id)
        doc = col.find_one({"_id": clip_id})
        return clean_doc(doc)
    except Exception as e:
        logger.error(f"Error finding clip by ID {clip_id}: {e}")
        return None

def resolve_thumbnail(clip_id):
    doc = get_clip_by_id(clip_id)
    if doc and doc.get("thumbnail") and os.path.exists(doc["thumbnail"]):
        return doc["thumbnail"]
    return None

def resolve_video_path(clip_id):
    doc = get_clip_by_id(clip_id)
    if doc and doc.get("video_path") and os.path.exists(doc["video_path"]):
        return doc["video_path"]
    return None
