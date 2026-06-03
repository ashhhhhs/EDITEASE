"""Business logic for the organized_videos collection."""

import datetime
import re
from collections import Counter

from bson import ObjectId

from database.organized_videos_schema import _get_col, slugify
from utils.logger import setup_logger

logger = setup_logger("organized_video_service")

# Hard limits for batch downloads
BATCH_MAX_FILES = 10


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize(doc: dict) -> dict:
    """Convert a Mongo doc to a JSON-serialisable dict."""
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    if doc.get("duplicate_of"):
        doc["duplicate_of"] = str(doc["duplicate_of"])
    return doc


def _literal_filename_search(search: str) -> dict:
    """Build a case-insensitive filename search that treats user input literally."""
    return {"$regex": re.escape(search), "$options": "i"}


def _access_conditions(
    *,
    uploader: str | None = None,
    accessible_video_names: list[str] | None = None,
) -> list[dict]:
    """Build organized-video visibility conditions for editor-owned/reviewed work."""
    conditions: list[dict] = []
    if uploader:
        conditions.append({"uploaded_by": uploader})

    video_names = sorted({
        str(name).strip()
        for name in (accessible_video_names or [])
        if str(name).strip()
    })
    if video_names:
        conditions.append({"safe_name": {"$in": [slugify(name) for name in video_names]}})
        conditions.extend(
            {
                "original_filename": {
                    "$regex": rf"^{re.escape(name)}(\.[^.]+)?$",
                    "$options": "i",
                }
            }
            for name in video_names[:200]
        )
    return conditions


def _apply_access_scope(
    query: dict,
    *,
    uploader: str | None = None,
    accessible_video_names: list[str] | None = None,
) -> dict:
    conditions = _access_conditions(
        uploader=uploader,
        accessible_video_names=accessible_video_names,
    )
    if conditions:
        query.setdefault("$and", []).append({"$or": conditions})
    return query


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------

def list_organized_videos(
    *,
    label: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    uploader: str | None = None,
    accessible_video_names: list[str] | None = None,
    requester_id: str | None = None,
    is_admin: bool = False,
    is_duplicate: bool | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict:
    """Return a paginated, filtered list of organized videos."""
    col = _get_col()
    page = max(1, page)
    limit = max(1, min(limit, 100))
    skip = (page - 1) * limit

    query: dict = {}
    if label:
        query["dominant_label"] = label
    if is_duplicate is True:
        query["status"] = "duplicate"
    elif is_duplicate is False:
        query["status"] = {"$ne": "duplicate"}
    if search:
        query["original_filename"] = _literal_filename_search(search)
    if from_date or to_date:
        date_q: dict = {}
        if from_date:
            date_q["$gte"] = from_date
        if to_date:
            date_q["$lte"] = to_date
        query["created_at"] = date_q
    query = _apply_access_scope(
        query,
        uploader=uploader,
        accessible_video_names=accessible_video_names,
    )

    cursor = col.find(query).sort("created_at", -1).skip(skip).limit(limit)
    docs = [_serialize(d) for d in cursor]
    for doc in docs:
        doc["can_delete"] = bool(is_admin or (requester_id and doc.get("uploaded_by") == requester_id))
    total = col.count_documents(query)

    return {"videos": docs, "total": total, "page": page, "limit": limit}


def get_organized_video(video_id: str) -> dict | None:
    """Return a single organized_videos record by _id string."""
    col = _get_col()
    try:
        doc = col.find_one({"_id": ObjectId(video_id)})
    except Exception:
        return None
    return _serialize(doc) if doc else None


def _summarize_scenes(scenes: list[dict], video_name: str = "") -> tuple[str, dict]:
    """Rebuild organized-video metadata from the latest reviewed scene records."""
    scenes = [scene for scene in scenes if isinstance(scene, dict)]

    def scene_label(scene: dict) -> str:
        return scene.get("manual_scene_label") or scene.get("scene_label") or "other"

    confident_labels = [
        scene_label(scene)
        for scene in scenes
        if scene.get("reviewed") is True
    ]
    if not confident_labels:
        confident_labels = [scene_label(scene) for scene in scenes]

    dominant_label = Counter(confident_labels).most_common(1)[0][0] if confident_labels else "other"
    label_dist = dict(Counter(scene_label(scene) for scene in scenes))

    dominant_emotion_votes = Counter(
        scene.get("manual_emotion") or scene.get("dominant_emotion_overall")
        for scene in scenes
        if scene.get("manual_emotion") or scene.get("dominant_emotion_overall")
    )
    dominant_emotion = dominant_emotion_votes.most_common(1)[0][0] if dominant_emotion_votes else "none"

    scene_confidences = []
    for scene in scenes:
        try:
            scene_confidences.append(float(scene.get("scene_confidence", 0) or 0))
        except (TypeError, ValueError):
            scene_confidences.append(0.0)
    avg_conf = sum(scene_confidences) / max(len(scenes), 1)

    face_scene_count = sum(
        1
        for scene in scenes
        if scene.get("faces", {}).get("face_present_any", False)
    )

    distinct_significant_labels = [label for label, count in label_dist.items() if count > 0]
    if len(distinct_significant_labels) >= 3:
        logger.info(
            "High scene diversity (%s types) detected while syncing %s. Categorizing as 'edited'.",
            len(distinct_significant_labels),
            video_name or "video",
        )
        dominant_label = "edited"
        action_taken = "review_sync_detected_by_variety"
    else:
        action_taken = "review_sync"

    return dominant_label, {
        "dominant_label": dominant_label,
        "dominant_emotion": dominant_emotion,
        "dominant_emotion_confidence": None,
        "average_confidence": round(avg_conf, 2),
        "total_scenes_detected": len(scenes),
        "label_distribution": label_dist,
        "action_taken": action_taken,
        "has_faces": face_scene_count > 0,
        "face_scene_count": face_scene_count,
        "face_scene_ratio": round(face_scene_count / max(len(scenes), 1), 3),
    }


def sync_organized_video_from_scenes(
    video_name: str,
    scenes: list[dict],
    *,
    uploader: str | None = None,
) -> dict:
    """Move the organized-video record to the current reviewed dominant label."""
    if not video_name:
        return {"ok": False, "updated_count": 0, "reason": "missing video name"}

    dominant_label, ai_metadata = _summarize_scenes(scenes, video_name)
    safe_name = slugify(video_name)
    filename_pattern = rf"^{re.escape(video_name)}(\.[^.]+)?$"

    query: dict = {
        "$or": [
            {"safe_name": safe_name},
            {"original_filename": {"$regex": filename_pattern, "$options": "i"}},
        ],
    }
    if uploader:
        query["uploaded_by"] = uploader

    update = {
        "$set": {
            "dominant_label": dominant_label,
            "download_name": f"{dominant_label}_{safe_name}.mp4",
            "ai_metadata": ai_metadata,
            "review_synced_at": datetime.datetime.utcnow().isoformat(),
        }
    }

    col = _get_col()
    res = col.update_many(query, update)
    return {
        "ok": True,
        "updated_count": res.modified_count,
        "dominant_label": dominant_label,
        "ai_metadata": ai_metadata,
    }


def delete_organized_videos(
    ids: list[str],
    *,
    requester_id: str | None = None,
    is_admin: bool = False,
) -> dict:
    """Delete organized-video records within the caller's visible scope.

    Editors can delete only their own uploads. Admins can delete any organized
    video record. Cloudinary assets are removed only when no remaining record
    references the same public ID, which keeps duplicate records from breaking
    shared assets.
    """
    if not isinstance(ids, list):
        return {"error": "ids must be a list.", "status": 400}
    if not ids:
        return {"error": "Select at least one video to delete.", "status": 400}

    object_ids = []
    for video_id in ids:
        if not ObjectId.is_valid(video_id):
            return {"error": "One or more video IDs are invalid.", "status": 400}
        object_ids.append(ObjectId(video_id))

    col = _get_col()
    query: dict = {"_id": {"$in": object_ids}}
    if not is_admin:
        if not requester_id:
            return {"error": "Unauthorized.", "status": 401}
        query["uploaded_by"] = requester_id

    docs = list(col.find(query))
    if not docs:
        existing_count = col.count_documents({"_id": {"$in": object_ids}})
        if existing_count and not is_admin:
            return {
                "error": "Only the uploader or an admin can delete these videos.",
                "status": 403,
            }
        return {"error": "No matching videos found.", "status": 404}

    delete_ids = [doc["_id"] for doc in docs]
    public_ids = sorted({
        doc.get("cloudinary_public_id")
        for doc in docs
        if doc.get("cloudinary_public_id")
    })

    result = col.delete_many({"_id": {"$in": delete_ids}})

    deleted_assets = 0
    skipped_assets = 0
    failed_assets: list[str] = []
    if public_ids:
        from services import cloudinary_service

        for public_id in public_ids:
            if col.count_documents({"cloudinary_public_id": public_id}) > 0:
                skipped_assets += 1
                continue
            try:
                if cloudinary_service.delete_asset(public_id, resource_type="video"):
                    deleted_assets += 1
                else:
                    failed_assets.append(public_id)
            except Exception as exc:
                logger.warning("Failed to delete Cloudinary asset %s: %s", public_id, exc)
                failed_assets.append(public_id)

    not_deleted = len(ids) - result.deleted_count
    return {
        "ok": True,
        "deleted_count": result.deleted_count,
        "requested_count": len(ids),
        "not_deleted_count": not_deleted,
        "asset_deleted_count": deleted_assets,
        "asset_skipped_count": skipped_assets,
        "asset_failed_count": len(failed_assets),
    }


# ---------------------------------------------------------------------------
# Batch validation
# ---------------------------------------------------------------------------

def validate_batch_request(ids: list[str]) -> tuple[bool, str]:
    """
    Validate a batch download request.
    Returns (ok, error_message). error_message is empty string on success.
    """
    if not ids:
        return False, "No video IDs provided."
    if len(ids) > BATCH_MAX_FILES:
        return False, f"Batch download is limited to {BATCH_MAX_FILES} files. You selected {len(ids)}."
    col = _get_col()
    found = col.count_documents({"_id": {"$in": [ObjectId(i) for i in ids if ObjectId.is_valid(i)]}})
    if found != len(ids):
        return False, "One or more video IDs were not found."
    return True, ""


def get_zip_download_path(task_id: str) -> str | None:
    """Retrieve the temp ZIP file path stored in a completed build_zip_task record."""
    from services.task_service import tasks_col
    job = tasks_col.find_one({"task_id": task_id, "type": "build_zip"})
    if not job:
        return None
    return job.get("output_path")


# ---------------------------------------------------------------------------
# Processing logs (join organized_videos → tasks via batch_id)
# ---------------------------------------------------------------------------

def get_processing_logs(
    *,
    label: str | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 30,
    requester_id: str | None = None,
) -> dict:
    """Return processing logs for organized videos.
    Each entry merges organized_video record with its task record.
    """
    from pymongo import MongoClient
    import config

    col = _get_col()
    client = MongoClient(config.MONGO_URI)
    tasks_col = client[config.DB_NAME]["tasks"]

    page = max(1, page)
    limit = max(1, min(limit, 100))
    skip = (page - 1) * limit

    query: dict = {}
    if requester_id:
        query["uploaded_by"] = requester_id
    if label:
        query["dominant_label"] = label
    if search:
        query["original_filename"] = _literal_filename_search(search)

    cursor = col.find(query).sort("created_at", -1).skip(skip).limit(limit)
    total = col.count_documents(query)

    logs = []
    for doc in cursor:
        entry = {
            "id": str(doc["_id"]),
            "video_name": doc.get("display_name", doc.get("original_filename", "")),
            "original_filename": doc.get("original_filename", ""),
            "dominant_label": doc.get("dominant_label", "other"),
            "status": doc.get("status", ""),
            "file_hash": doc.get("file_hash", "")[:12] + "…" if doc.get("file_hash") else "",
            "created_at": doc.get("created_at", ""),
            "uploaded_by": doc.get("uploaded_by"),
            "batch_id": doc.get("batch_id"),
            "ai_metadata": doc.get("ai_metadata", {}),
        }
        # Enrich with task record if available
        if doc.get("batch_id"):
            task = tasks_col.find_one({"task_id": doc["batch_id"]})
            if task:
                entry["task_status"] = task.get("status", "UNKNOWN")
                entry["task_progress"] = task.get("progress_step", "")
                entry["task_created_at"] = task.get("created_at", "")
                entry["task_updated_at"] = task.get("updated_at", "")
                entry["task_error"] = task.get("error_message")
                # Compute processing duration
                if task.get("created_at") and task.get("updated_at"):
                    try:
                        from datetime import datetime
                        start = datetime.fromisoformat(task["created_at"])
                        end = datetime.fromisoformat(task["updated_at"])
                        entry["processing_seconds"] = round((end - start).total_seconds(), 1)
                    except Exception:
                        entry["processing_seconds"] = None
            else:
                entry["task_status"] = "NO_RECORD"
        else:
            entry["task_status"] = "NO_TASK"

        logs.append(entry)

    return {"logs": logs, "total": total, "page": page, "limit": limit}


# ---------------------------------------------------------------------------
# Per-label counts (for admin overview)
# ---------------------------------------------------------------------------

def get_label_counts(
    uploader: str | None = None,
    accessible_video_names: list[str] | None = None,
) -> dict:
    col = _get_col()
    match: dict = {"status": "organized"}
    match = _apply_access_scope(
        match,
        uploader=uploader,
        accessible_video_names=accessible_video_names,
    )
    pipeline = [
        {"$match": match},
        {"$group": {"_id": "$dominant_label", "count": {"$sum": 1}}},
    ]
    return {r["_id"]: r["count"] for r in col.aggregate(pipeline)}
