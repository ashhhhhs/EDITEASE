import os
import datetime
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

def _apply_review_scope(query, current_user=None):
    """Restrict review access for roles that should not see the whole queue."""
    if not current_user:
        return query

    role = current_user.get("role")
    if role == "reviewer":
        query["assigned_to"] = current_user.get("id")
    return query


def _can_review_doc(doc, current_user=None):
    if not current_user:
        return True
    role = current_user.get("role")
    if role in ("admin", "editor"):
        return True
    if role == "reviewer":
        return doc.get("assigned_to") == current_user.get("id")
    return False


def _reconcile_completed_review_requests(current_user=None):
    if not current_user or not hasattr(col, "update_many"):
        return 0

    role = current_user.get("role")
    scope = {}
    if role == "reviewer":
        scope["assigned_to"] = current_user.get("id")
    elif role == "editor":
        scope["$or"] = [
            {"assigned_to": current_user.get("id")},
            {"review_requested_by": current_user.get("id")},
        ]
    elif role != "admin":
        return 0

    completed_query = {
        "reviewed": True,
        "review_request_status": {"$in": ["open", "assigned"]},
        **scope,
    }
    resolved_unreviewed_query = {
        "reviewed": {"$ne": True},
        "review_request_status": "resolved",
        **scope,
    }

    now = datetime.datetime.utcnow().isoformat()
    try:
        completed_res = col.update_many(
            completed_query,
            {
                "$set": {
                    "review_request_status": "resolved",
                    "review_resolved_at": now,
                    "review_resolved_by": "system",
                    "review_resolution_note": "Auto-resolved because the clip was already marked reviewed.",
                    "review_resolution_seen_by_requester": False,
                    "review_resolution_seen_at": None,
                }
            },
        )
        resolved_res = col.update_many(
            resolved_unreviewed_query,
            {
                "$set": {
                    "reviewed": True,
                    "review_resolution_note": "Auto-marked reviewed because the request was already resolved.",
                }
            },
        )
        return completed_res.modified_count + resolved_res.modified_count
    except Exception as e:
        logger.error(f"Failed to reconcile completed review requests: {e}")
        return 0


def _add_or_clause(query, clauses):
    if "$or" not in query:
        query["$or"] = clauses
        return
    existing = query.pop("$or")
    query.setdefault("$and", []).append({"$or": existing})
    query["$and"].append({"$or": clauses})


def search_clips(filters, limit=100, current_user=None):
    limit = max(1, min(int(limit), 200))
    q = {}

    scene_label = filters.get("scene_label")
    if scene_label:
        q["scene_label"] = scene_label

    emotion = filters.get("emotion")
    if emotion:
        if emotion == "__NULL__":
            _add_or_clause(q, [
                {"dominant_emotion_overall": None},
                {"dominant_emotion_overall": {"$exists": False}}
            ])
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

    review_request_status = filters.get("review_request_status")
    if review_request_status:
        if review_request_status == "__NONE__":
            _add_or_clause(q, [
                {"review_request_status": {"$exists": False}},
                {"review_request_status": None},
            ])
        else:
            q["review_request_status"] = review_request_status

    assigned_to_me = filters.get("assigned_to_me")
    if assigned_to_me is not None and current_user:
        if isinstance(assigned_to_me, str):
            assigned_to_me = assigned_to_me.lower() in ("true", "1", "yes")
        if assigned_to_me:
            q["assigned_to"] = current_user.get("id")

    requested_by_me = filters.get("requested_by_me")
    if requested_by_me is not None and current_user:
        if isinstance(requested_by_me, str):
            requested_by_me = requested_by_me.lower() in ("true", "1", "yes")
        if requested_by_me:
            q["review_requested_by"] = current_user.get("id")

    resolution_unseen = filters.get("resolution_unseen")
    if resolution_unseen is not None:
        if isinstance(resolution_unseen, str):
            resolution_unseen = resolution_unseen.lower() in ("true", "1", "yes")
        if resolution_unseen:
            q["review_resolution_seen_by_requester"] = {"$ne": True}

    min_duration = filters.get("min_duration")
    max_duration = filters.get("max_duration")
    if min_duration is not None or max_duration is not None:
        q["duration_sec"] = {}
        if min_duration is not None:
            q["duration_sec"]["$gte"] = float(min_duration)
        if max_duration is not None:
            q["duration_sec"]["$lte"] = float(max_duration)
            
    if (
        current_user
        and (
            filters.get("review_request_status") in ("open", "assigned", "resolved")
            or filters.get("assigned_to_me") is not None
            or filters.get("requested_by_me") is not None
        )
    ):
        _reconcile_completed_review_requests(current_user)

    # Pagination
    page = max(1, int(filters.get("page", 1)))
    limit = max(1, min(int(limit), 200)) # Default max 200 via param
    skip = (page - 1) * limit

    q = _apply_review_scope(q, current_user)

    total = col.count_documents(q)
    cursor = col.find(q).sort("duration_sec", -1).skip(skip).limit(limit)
    results = [clean_doc(d) for d in cursor]
    return {"count": len(results), "total": total, "page": page, "limit": limit, "query": q, "results": results}


def request_admin_review(keys, reason, current_user=None):
    if not keys:
        return {"error": "scene_keys required", "status": 400}
    if not current_user or current_user.get("role") not in ("editor", "reviewer"):
        return {"error": "Only editors and reviewers can request admin review.", "status": 403}

    reason = (reason or "").strip()
    if not reason:
        return {"error": "reason required", "status": 400}
    if len(reason) > 500:
        return {"error": "reason must be 500 characters or fewer", "status": 400}

    now = datetime.datetime.utcnow().isoformat()
    update_fields = {
        "review_request_status": "open",
        "review_request_reason": reason,
        "review_requested_at": now,
        "review_requested_by": current_user.get("id"),
        "review_requested_by_name": current_user.get("name"),
        "review_requested_by_email": current_user.get("email"),
        "review_requested_by_role": current_user.get("role"),
        "review_resolved_at": None,
        "review_resolved_by": None,
        "review_resolution_note": None,
        "review_resolution_seen_by_requester": False,
        "review_resolution_seen_at": None,
    }

    query = {"_key": {"$in": keys}}
    query = _apply_review_scope(query, current_user)
    res = col.update_many(query, {"$set": update_fields})
    return {"ok": True, "requested_count": res.modified_count, "fields": update_fields}


def resolve_review_requests(keys, status, note="", current_user=None):
    if not keys:
        return {"error": "scene_keys required", "status": 400}
    if not current_user or current_user.get("role") != "admin":
        return {"error": "Only admins can resolve review requests.", "status": 403}
    if status not in ("resolved", "dismissed"):
        return {"error": "status must be resolved or dismissed", "status": 400}

    now = datetime.datetime.utcnow().isoformat()
    update_fields = {
        "review_request_status": status,
        "review_resolved_at": now,
        "review_resolved_by": current_user.get("id"),
        "review_resolution_note": (note or "").strip()[:500],
        "review_resolution_seen_by_requester": False,
        "review_resolution_seen_at": None,
    }
    if status == "resolved":
        update_fields["reviewed"] = True

    res = col.update_many(
        {"_key": {"$in": keys}, "review_request_status": {"$in": ["open", "assigned"]}},
        {"$set": update_fields},
    )
    return {"ok": True, "resolved_count": res.modified_count, "fields": update_fields}


def assign_review_requests(keys, assignee, note="", current_user=None):
    if not keys:
        return {"error": "scene_keys required", "status": 400}
    if not current_user or current_user.get("role") != "admin":
        return {"error": "Only admins can assign review requests.", "status": 403}
    if not assignee or assignee.get("role") not in ("editor", "reviewer") or not assignee.get("is_active", True):
        return {"error": "Assignee must be an active editor or reviewer.", "status": 400}

    now = datetime.datetime.utcnow().isoformat()
    assignee_id = assignee.get("id") or assignee.get("_id")
    update_fields = {
        "assigned_to": str(assignee_id),
        "review_request_status": "assigned",
        "review_assigned_at": now,
        "review_assigned_by": current_user.get("id"),
        "review_assigned_to": str(assignee_id),
        "review_assigned_to_name": assignee.get("name"),
        "review_assigned_to_email": assignee.get("email"),
        "review_assigned_to_role": assignee.get("role"),
        "review_assignment_note": (note or "").strip()[:500],
    }
    res = col.update_many(
        {"_key": {"$in": keys}, "review_request_status": {"$in": ["open", "assigned"]}},
        {"$set": update_fields},
    )
    return {"ok": True, "assigned_count": res.modified_count, "assignee": {
        "id": str(assignee_id),
        "name": assignee.get("name"),
        "email": assignee.get("email"),
        "role": assignee.get("role"),
    }, "fields": update_fields}


def request_peer_review(keys, assignee, reason, current_user=None):
    if not keys:
        return {"error": "scene_keys required", "status": 400}
    if not current_user or current_user.get("role") != "editor":
        return {"error": "Only editors can request peer review.", "status": 403}
    if not assignee or assignee.get("role") not in ("editor", "reviewer") or not assignee.get("is_active", True):
        return {"error": "Assignee must be an active editor or reviewer.", "status": 400}

    assignee_id = str(assignee.get("id") or assignee.get("_id"))
    if assignee_id == str(current_user.get("id")):
        return {"error": "Cannot request peer review from yourself.", "status": 400}

    reason = (reason or "").strip()
    if not reason:
        return {"error": "reason required", "status": 400}
    if len(reason) > 500:
        return {"error": "reason must be 500 characters or fewer", "status": 400}

    now = datetime.datetime.utcnow().isoformat()
    update_fields = {
        "assigned_to": assignee_id,
        "review_request_status": "assigned",
        "review_request_reason": reason,
        "review_requested_at": now,
        "review_requested_by": current_user.get("id"),
        "review_requested_by_name": current_user.get("name"),
        "review_requested_by_email": current_user.get("email"),
        "review_requested_by_role": current_user.get("role"),
        "review_assigned_at": now,
        "review_assigned_by": current_user.get("id"),
        "review_assigned_to": assignee_id,
        "review_assigned_to_name": assignee.get("name"),
        "review_assigned_to_email": assignee.get("email"),
        "review_assigned_to_role": assignee.get("role"),
        "review_assignment_note": reason,
        "review_resolved_at": None,
        "review_resolved_by": None,
        "review_resolution_note": None,
        "review_resolution_seen_by_requester": False,
        "review_resolution_seen_at": None,
    }

    res = col.update_many({"_key": {"$in": keys}}, {"$set": update_fields})
    return {"ok": True, "requested_count": res.modified_count, "assignee": {
        "id": assignee_id,
        "name": assignee.get("name"),
        "email": assignee.get("email"),
        "role": assignee.get("role"),
    }, "fields": update_fields}


def acknowledge_resolved_requests(current_user=None):
    if not current_user or current_user.get("role") not in ("editor", "reviewer"):
        return {"error": "Only editors and reviewers can acknowledge resolved requests.", "status": 403}

    now = datetime.datetime.utcnow().isoformat()
    res = col.update_many(
        {
            "review_requested_by": current_user.get("id"),
            "review_request_status": "resolved",
            "review_resolution_seen_by_requester": {"$ne": True},
        },
        {
            "$set": {
                "review_resolution_seen_by_requester": True,
                "review_resolution_seen_at": now,
            }
        },
    )
    return {"ok": True, "acknowledged_count": res.modified_count}


def bulk_update_clips(keys, update_data, current_user=None):
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
        
    query = {"_key": {"$in": keys}}
    query = _apply_review_scope(query, current_user)

    res = col.update_many(query, {"$set": update_fields})

    auto_resolved_count = 0
    if update_fields.get("reviewed") is True and current_user:
        is_admin = current_user.get("role") == "admin"
        resolution_fields = {
            "review_request_status": "resolved",
            "review_resolved_at": datetime.datetime.utcnow().isoformat(),
            "review_resolved_by": current_user.get("id"),
            "review_resolution_note": "Marked reviewed by admin." if is_admin else "Marked reviewed by assigned reviewer.",
            "review_resolution_seen_by_requester": False,
            "review_resolution_seen_at": None,
        }
        resolution_query = {
            "_key": {"$in": keys},
        }
        if is_admin:
            resolution_query["review_request_status"] = {"$in": ["open", "assigned"]}
        else:
            resolution_query["assigned_to"] = current_user.get("id")
            resolution_query["review_request_status"] = "assigned"

        resolution_res = col.update_many(
            resolution_query,
            {"$set": resolution_fields},
        )
        auto_resolved_count = resolution_res.modified_count

    return {
        "ok": True,
        "updated_count": res.modified_count,
        "auto_resolved_count": auto_resolved_count,
        "fields": update_fields,
    }

def update_clip(video, scene_id, data, current_user=None):
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
    if not _can_review_doc(doc, current_user):
        return {"error": "access denied", "status": 403}

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

    if (
        update_fields.get("reviewed") is True
        and current_user
        and (
            (
                current_user.get("role") == "admin"
                and doc.get("review_request_status") in ("open", "assigned")
            )
            or (
                doc.get("review_request_status") == "assigned"
                and doc.get("assigned_to") == current_user.get("id")
            )
        )
    ):
        update_fields["review_request_status"] = "resolved"
        update_fields["review_resolved_at"] = datetime.datetime.utcnow().isoformat()
        update_fields["review_resolved_by"] = current_user.get("id")
        update_fields["review_resolution_note"] = (
            "Marked reviewed by admin."
            if current_user.get("role") == "admin"
            else "Marked reviewed by assigned reviewer."
        )
        update_fields["review_resolution_seen_by_requester"] = False
        update_fields["review_resolution_seen_at"] = None

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
    """Return Cloudinary thumbnail URL if available, else local path."""
    doc = get_clip_by_id(clip_id)
    if not doc:
        return None
    # Prefer Cloudinary URL (cloud-hosted)
    cloud_url = doc.get("thumbnail_url")
    if cloud_url:
        return cloud_url
    # Fallback: legacy local path
    local = doc.get("thumbnail")
    if local and os.path.exists(local):
        return local
    return None

def resolve_video_path(clip_id):
    """Return Cloudinary video URL if available, else local path."""
    doc = get_clip_by_id(clip_id)
    if not doc:
        return None
    # Prefer Cloudinary URL (cloud-hosted)
    cloud_url = doc.get("cloudinary_url")
    if cloud_url:
        return cloud_url
    # Fallback: legacy local path
    local = doc.get("video_path")
    if local and os.path.exists(local):
        return local
    return None
