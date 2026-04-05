"""
Schema helper for the `organized_videos` MongoDB collection.

Each document represents a full video that has been processed and
organized into Cloudinary under editease/organized-videos/<label>/<hash>__<safe-name>.

Fields
------
original_filename : str   Raw filename as uploaded by the user.
display_name      : str   Human-readable name shown in the UI.
safe_name         : str   Slugified name used in Cloudinary paths.
file_hash         : str   SHA-256 hex digest of the video bytes — uniqueness key.
cloudinary_public_id : str  Full Cloudinary public ID.
cloudinary_url    : str   Secure CDN URL.
dominant_label    : str   Top classification label (e.g. "interview", "product").
status            : str   "organized" | "duplicate" | "error"
uploaded_by       : str | None   User _id string of the uploader.
created_at        : str   UTC ISO-8601 timestamp.
duplicate_of      : str | None   _id of the original document if this is a duplicate.
batch_id          : str | None   Celery task ID that produced this record.
download_name     : str   Friendly filename used in ZIP / download headers.
"""

import datetime
import re

import config
from utils.logger import setup_logger

logger = setup_logger("organized_videos_schema")

_client = None


def _get_col():
    """Return the `organized_videos` collection, creating indexes on first call."""
    global _client
    from pymongo import MongoClient, ASCENDING
    if _client is None:
        _client = MongoClient(config.MONGO_URI)
    db = _client[config.DB_NAME]
    col = db["organized_videos"]
    try:
        # Uniqueness is enforced at application level (duplicates are linked records),
        # so file_hash is indexed but NOT unique in Mongo — two docs can share a hash
        # when the second is a duplicate record.
        col.create_index([("file_hash", ASCENDING)])
        col.create_index([("dominant_label", ASCENDING)])
        col.create_index([("uploaded_by", ASCENDING)])
        col.create_index([("created_at", ASCENDING)])
        col.create_index([("status", ASCENDING)])
    except Exception as exc:
        logger.warning("Could not create organized_videos indexes: %s", exc)
    return col


def slugify(text: str) -> str:
    """Convert a string to a URL/path-safe slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:80]


def build_doc(
    *,
    original_filename: str,
    file_hash: str,
    cloudinary_public_id: str,
    cloudinary_url: str,
    dominant_label: str,
    status: str = "organized",
    uploaded_by: str | None = None,
    duplicate_of: str | None = None,
    batch_id: str | None = None,
    ai_metadata: dict | None = None,
) -> dict:
    """Return a ready-to-insert organized_videos document."""
    base_name = original_filename.rsplit(".", 1)[0] if "." in original_filename else original_filename
    safe_name = slugify(base_name)
    display_name = base_name.replace("-", " ").replace("_", " ").title()
    download_name = f"{dominant_label}_{safe_name}.mp4"

    return {
        "original_filename": original_filename,
        "display_name": display_name,
        "safe_name": safe_name,
        "file_hash": file_hash,
        "cloudinary_public_id": cloudinary_public_id,
        "cloudinary_url": cloudinary_url,
        "dominant_label": dominant_label,
        "status": status,
        "uploaded_by": uploaded_by,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "duplicate_of": duplicate_of,
        "batch_id": batch_id,
        "download_name": download_name,
        "ai_metadata": ai_metadata or {},
    }
