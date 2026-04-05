import os
from celery import Celery
from pymongo import MongoClient
import datetime

import config
from utils.logger import setup_logger

logger = setup_logger("celery_worker")

db_client = MongoClient(config.MONGO_URI)
tasks_col = db_client[config.DB_NAME]["tasks"]

def _update_task(task_id, **kwargs):
    kwargs["updated_at"] = datetime.datetime.utcnow().isoformat()
    tasks_col.update_one({"task_id": task_id}, {"$set": kwargs})

# Initialize Celery app
celery_app = Celery(
    "editease_tasks",
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND
)

# Optional configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_hijack_root_logger=False
)

@celery_app.task(bind=True, name="process_video_task")
def process_video_task(self, video_path_str: str, base_dir_str: str):
    """
    Background task to run the EditEase video processing pipeline.
    """
    from pipeline.processing.run_pipeline import process_video
    logger.info(f"Starting Celery task for video: {video_path_str}")
    _update_task(self.request.id, status="STARTED", progress_step="processing")
    
    try:
        def on_progress(msg):
            self.update_state(state="PROGRESS", meta={"step": "processing", "message": msg})
            _update_task(self.request.id, progress_step=msg)

        process_video(video_path_str, base_dir_str, progress_callback=on_progress)
        logger.info(f"Finished Celery task for video: {video_path_str}")
        _update_task(self.request.id, status="SUCCESS", progress_step="done")
        return {"status": "success", "video_path": video_path_str}
    except Exception as e:
        logger.error(f"Celery task failed for {video_path_str}: {e}", exc_info=True)
        _update_task(self.request.id, status="FAILURE", error_message=str(e), progress_step="error")
        raise e


@celery_app.task(bind=True, name="auto_organize_task")
def auto_organize_task(self, video_path_str: str, base_dir_str: str, user_id: str | None = None):
    """
    One-click auto-organize: process video → copy full video into dominant scene type folder.
    This is the Editor mode flow.

    Execution order:
      1. Compute file hash (before any upload) — prevents filename collisions.
      2. Check organized_videos for an existing hash — detect duplicates early.
      3. Run pipeline (uses hash-safe Cloudinary public ID for first upload).
      4. Determine dominant label from scene index.
      5. Move video from editease/videos/<hash>__<safe> → editease/organized-videos/<label>/<hash>__<safe>.
      6. Write organized_videos record (or duplicate record if hash already exists).
    """
    import json
    import hashlib
    from pathlib import Path
    from database.organized_videos_schema import _get_col, build_doc, slugify

    video_name = os.path.splitext(os.path.basename(video_path_str))[0]
    original_filename = os.path.basename(video_path_str)
    logger.info(f"Auto-organize started for: {video_name}")

    # ── Step 1: Compute file hash before any upload ───────────────────────────
    _update_task(self.request.id, status="STARTED", progress_step="hashing")
    try:
        with open(video_path_str, "rb") as fh:
            file_hash = hashlib.sha256(fh.read()).hexdigest()
        safe_name = slugify(video_name)
        logger.info(f"File hash for {video_name}: {file_hash[:12]}...")
    except Exception as e:
        logger.error(f"Failed to hash video {video_path_str}: {e}")
        _update_task(self.request.id, status="FAILURE", error_message=str(e), progress_step="error")
        raise e

    # ── Step 2: Process video (pipeline uses the hash-safe public ID) ─────────
    self.update_state(state="PROGRESS", meta={"step": "processing", "message": "Analyzing video..."})
    _update_task(self.request.id, status="STARTED", progress_step="processing")
    from pipeline.processing.run_pipeline import process_video
    try:
        def on_progress(msg):
            self.update_state(state="PROGRESS", meta={"step": "processing", "message": msg})
            _update_task(self.request.id, progress_step=msg)

        process_video(video_path_str, base_dir_str, file_hash=file_hash, progress_callback=on_progress)
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        _update_task(self.request.id, status="FAILURE", error_message=str(e), progress_step="error")
        raise e

    # ── Step 3: Read scene index ──────────────────────────────────────────────
    self.update_state(state="PROGRESS", meta={"step": "organizing", "message": "Organizing clips..."})
    _update_task(self.request.id, progress_step="organizing")
    index_path = os.path.join(base_dir_str, "scene_indexes", f"{video_name}_scene_index.json")
    if not os.path.exists(index_path):
        _update_task(self.request.id, status="FAILURE", error_message="Scene index not generated", progress_step="error")
        return {"status": "error", "message": "Scene index not generated"}

    with open(index_path, "r", encoding="utf-8") as f:
        scenes = json.load(f)

    # ── Step 4: Determine dominant label ─────────────────────────────────────
    from collections import Counter
    confident_labels = [s.get("scene_label", "other") for s in scenes if s.get("reviewed") is True]
    if not confident_labels:
        confident_labels = [s.get("scene_label", "other") for s in scenes]
    dominant_label = Counter(confident_labels).most_common(1)[0][0] if confident_labels else "other"

    dominant_emotion_votes = Counter([s.get("dominant_emotion_overall") for s in scenes if s.get("dominant_emotion_overall")])
    dominant_emotion = dominant_emotion_votes.most_common(1)[0][0] if dominant_emotion_votes else "none"
    avg_conf = sum(s.get("scene_confidence", 0) for s in scenes) / max(len(scenes), 1)
    
    ai_metadata = {
        "dominant_label": dominant_label,
        "dominant_emotion": dominant_emotion,
        "average_confidence": round(avg_conf, 2),
        "total_scenes_detected": len(scenes),
        "label_distribution": dict(Counter([s.get("scene_label", "other") for s in scenes])),
        "action_taken": scenes[0].get("scene_debug", {}).get("agent_action", "unknown") if scenes else "unknown",
        "has_faces": any(s.get("faces", {}).get("face_present_any", False) for s in scenes)
    }

    # ── Step 5: Duplicate detection ───────────────────────────────────────────
    col = _get_col()
    existing = col.find_one({"file_hash": file_hash, "status": "organized"})

    if existing:
        # Same bytes already organized — create a lightweight duplicate record
        logger.info(f"Duplicate detected for hash {file_hash[:12]}... — reusing existing asset")
        dup_doc = build_doc(
            original_filename=original_filename,
            file_hash=file_hash,
            cloudinary_public_id=existing["cloudinary_public_id"],
            cloudinary_url=existing["cloudinary_url"],
            dominant_label=existing["dominant_label"],
            status="duplicate",
            uploaded_by=user_id,
            duplicate_of=str(existing["_id"]),
            batch_id=self.request.id,
            ai_metadata=ai_metadata,
        )
        col.insert_one(dup_doc)
        _update_task(
            self.request.id,
            status="SUCCESS",
            progress_step="done",
            output_path=existing["cloudinary_public_id"],
        )
        # Clean up local file
        try:
            if os.path.exists(video_path_str):
                os.remove(video_path_str)
        except Exception as e:
            logger.warning("Failed to remove local video %s: %s", video_path_str, e)
        return {
            "status": "duplicate",
            "video": video_name,
            "dominant_label": existing["dominant_label"],
            "duplicate_of": str(existing["_id"]),
        }

    # ── Step 6: Move video to organized folder ────────────────────────────────
    from services import cloudinary_service
    old_pub_id = f"editease/videos/{file_hash}__{safe_name}"
    new_pub_id = f"editease/organized-videos/{dominant_label}/{file_hash}__{safe_name}"
    cloudinary_url, actual_pub_id = cloudinary_service.move_video_returning_id(old_pub_id, new_pub_id)

    if not cloudinary_url:
        # Move failed — log and continue; local file will still be cleaned up
        logger.error(f"Failed to move Cloudinary video for {video_name}")
        actual_pub_id = new_pub_id  # use intended path so record is still useful

    # ── Step 7: Write organized_videos record ─────────────────────────────────
    doc = build_doc(
        original_filename=original_filename,
        file_hash=file_hash,
        cloudinary_public_id=actual_pub_id or new_pub_id,
        cloudinary_url=cloudinary_url or "",
        dominant_label=dominant_label,
        status="organized",
        uploaded_by=user_id,
        batch_id=self.request.id,
        ai_metadata=ai_metadata,
    )
    col.insert_one(doc)
    logger.info(f"Wrote organized_videos record for {video_name} ({dominant_label})")

    # ── Step 8: Clean up local file ───────────────────────────────────────────
    try:
        if os.path.exists(video_path_str):
            os.remove(video_path_str)
            logger.info("Removed original video from local storage: %s", video_path_str)
    except Exception as e:
        logger.warning("Failed to remove original video %s: %s", video_path_str, e)

    _update_task(self.request.id, status="SUCCESS", progress_step="done", output_path=actual_pub_id)
    return {
        "status": "success",
        "video": video_name,
        "dominant_label": dominant_label,
        "export_path": actual_pub_id,
    }


@celery_app.task(bind=True, name="build_zip_task")
def build_zip_task(self, video_ids: list, user_id: str | None = None):
    """
    Build a ZIP archive of selected organized videos for batch download.
    Hard limit: max 10 files (enforced at API level before dispatch).
    Files streamed from Cloudinary to disk temp files, not into memory.
    """
    import tempfile
    import zipfile
    import requests as http_requests
    from bson import ObjectId
    from database.organized_videos_schema import _get_col

    logger.info(f"build_zip_task started for {len(video_ids)} videos")
    tasks_col.update_one({"task_id": self.request.id}, {"$set": {"type": "build_zip", "status": "STARTED", "progress_step": "building"}})

    col = _get_col()
    docs = list(col.find({"_id": {"$in": [ObjectId(i) for i in video_ids if ObjectId.is_valid(i)]}}))

    if not docs:
        tasks_col.update_one({"task_id": self.request.id}, {"$set": {"status": "FAILURE", "error_message": "No valid records found", "progress_step": "error"}})
        return {"status": "error", "message": "No valid records found"}

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".zip", prefix="editease_batch_")
    os.close(tmp_fd)

    try:
        with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for idx, doc in enumerate(docs, start=1):
                label = doc.get("dominant_label", "other")
                download_name = doc.get("download_name") or f"{doc.get('safe_name', 'video')}.mp4"
                arcname = f"organized-videos/{label}/{download_name}"
                url = doc.get("cloudinary_url", "")
                self.update_state(state="PROGRESS", meta={"step": "downloading", "current": idx, "total": len(docs)})
                tasks_col.update_one({"task_id": self.request.id}, {"$set": {"progress_step": f"downloading {idx}/{len(docs)}"}})
                if not url:
                    logger.warning("No URL for doc %s, skipping", str(doc["_id"]))
                    continue
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as vid_tmp:
                    vid_tmp_path = vid_tmp.name
                try:
                    resp = http_requests.get(url, stream=True, timeout=120)
                    resp.raise_for_status()
                    with open(vid_tmp_path, "wb") as fout:
                        for chunk in resp.iter_content(chunk_size=262144):
                            fout.write(chunk)
                    zf.write(vid_tmp_path, arcname=arcname)
                finally:
                    try:
                        os.remove(vid_tmp_path)
                    except Exception:
                        pass
    except Exception as exc:
        logger.error("build_zip_task failed: %s", exc, exc_info=True)
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        tasks_col.update_one({"task_id": self.request.id}, {"$set": {"status": "FAILURE", "error_message": str(exc), "progress_step": "error"}})
        raise exc

    tasks_col.update_one({"task_id": self.request.id}, {"$set": {"status": "SUCCESS", "progress_step": "done", "output_path": tmp_path}})
    logger.info("build_zip_task complete: %s", tmp_path)
    return {"status": "success", "zip_path": tmp_path, "file_count": len(docs)}
