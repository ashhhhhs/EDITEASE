"""Business logic for the organized_videos collection."""

import io
import zipfile
import requests
import datetime

from bson import ObjectId

from database.organized_videos_schema import _get_col
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


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------

def list_organized_videos(
    *,
    label: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    uploader: str | None = None,
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
    if uploader:
        query["uploaded_by"] = uploader
    if is_duplicate is True:
        query["status"] = "duplicate"
    elif is_duplicate is False:
        query["status"] = {"$ne": "duplicate"}
    if search:
        query["original_filename"] = {"$regex": search, "$options": "i"}
    if from_date or to_date:
        date_q: dict = {}
        if from_date:
            date_q["$gte"] = from_date
        if to_date:
            date_q["$lte"] = to_date
        query["created_at"] = date_q

    cursor = col.find(query).sort("created_at", -1).skip(skip).limit(limit)
    docs = [_serialize(d) for d in cursor]
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
# Per-label counts (for admin overview)
# ---------------------------------------------------------------------------

def get_label_counts() -> dict:
    col = _get_col()
    pipeline = [
        {"$match": {"status": "organized"}},
        {"$group": {"_id": "$dominant_label", "count": {"$sum": 1}}},
    ]
    return {r["_id"]: r["count"] for r in col.aggregate(pipeline)}
