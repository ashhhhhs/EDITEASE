import os
from collections import Counter
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
    _update_task(self.request.id, status="STARTED", progress_step="Preparing pipeline...")
    
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


def check_if_edited_by_metadata(video_path: str) -> bool:
    """Check video metadata for editing software signatures via ffprobe."""
    import subprocess
    import json
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', 
            '-show_format', video_path
        ]
        res = subprocess.check_output(cmd).decode('utf-8')
        data = json.loads(res)
        fmt_tags = data.get('format', {}).get('tags', {})
        # Check encoder/software tags
        encoder = str(fmt_tags.get('encoder', '')).lower()
        software = str(fmt_tags.get('software', '')).lower()
        markers = ['adobe', 'premiere', 'resolve', 'davinci', 'final cut', 'fcp', 'handbrake', 'lavf', 'capcut', 'imovie']
        if any(sw in encoder for sw in markers) or any(sw in software for sw in markers):
            return True
        return False
    except Exception:
        return False

def check_if_edited_by_filename(filename: str) -> bool:
    """Check filename for strong editing/export signals.

    Only matches explicit, underscore-or-hyphen-anchored markers so that
    incidental substrings (e.g. "_v2" version suffix on a raw clip) do not
    misroute footage into the edited bucket. Bare keywords like "final" or
    "edit" were removed because they false-positive on common filenames.
    """
    import re
    pattern = (
        r'(?:^|[_\-\s])'                                  # boundary
        r'(final_cut|fcp|master_edit|finished_cut|'
        r'final_render|edited_video|exported_video|'
        r'_premiere|_resolve|_davinci|_capcut|_imovie)'
        r'(?:[_\-\s\.]|$)'                                # boundary
    )
    return bool(re.search(pattern, filename.lower()))


def build_ai_metadata_from_scenes(scenes: list[dict], video_name: str = "") -> tuple[str, dict]:
    """
    Summarize processed scenes into the organized video label and metadata.

    Kept pure so the rule set can be unit-tested without Celery, Cloudinary,
    MongoDB writes, or a full video-processing run.
    """
    scenes = [scene for scene in scenes if isinstance(scene, dict)]

    confident_labels = [
        scene.get("scene_label", "other")
        for scene in scenes
        if scene.get("reviewed") is True
    ]
    if not confident_labels:
        confident_labels = [scene.get("scene_label", "other") for scene in scenes]

    dominant_label = Counter(confident_labels).most_common(1)[0][0] if confident_labels else "other"

    dominant_emotion_votes = Counter(
        scene.get("dominant_emotion_overall")
        for scene in scenes
        if scene.get("dominant_emotion_overall")
    )
    dominant_emotion = (
        dominant_emotion_votes.most_common(1)[0][0]
        if dominant_emotion_votes else "none"
    )

    dominant_emotion_conf_samples = []
    if dominant_emotion != "none":
        for scene in scenes:
            for sample in scene.get("emotion_timeline") or []:
                if (
                    sample.get("emotion") == dominant_emotion
                    and sample.get("confidence") is not None
                ):
                    try:
                        dominant_emotion_conf_samples.append(float(sample["confidence"]))
                    except (TypeError, ValueError):
                        continue

    dominant_emotion_confidence = (
        round(sum(dominant_emotion_conf_samples) / len(dominant_emotion_conf_samples), 2)
        if dominant_emotion_conf_samples else None
    )

    scene_confidences = []
    for scene in scenes:
        try:
            scene_confidences.append(float(scene.get("scene_confidence", 0) or 0))
        except (TypeError, ValueError):
            scene_confidences.append(0.0)
    avg_conf = sum(scene_confidences) / max(len(scenes), 1)

    face_scene_count = sum(
        1 for scene in scenes
        if scene.get("faces", {}).get("face_present_any", False)
    )
    face_sample_hits = 0
    face_sample_total = 0
    for scene in scenes:
        timeline = scene.get("emotion_timeline") or []
        face_sample_total += len(timeline)
        face_sample_hits += sum(1 for sample in timeline if sample.get("face_detected") is True)

    label_dist = dict(Counter(scene.get("scene_label", "other") for scene in scenes))
    distinct_significant_labels = [label for label, count in label_dist.items() if count > 0]
    if len(distinct_significant_labels) >= 3:
        logger.info(
            "High scene diversity (%s types) detected for %s. Auto-categorizing as 'edited'.",
            len(distinct_significant_labels),
            video_name or "video",
        )
        dominant_label = "edited"
        action_taken = "auto_detected_by_variety"
    else:
        action_taken = (
            scenes[0].get("scene_debug", {}).get("agent_action", "unknown")
            if scenes else "unknown"
        )

    ai_metadata = {
        "dominant_label": dominant_label,
        "dominant_emotion": dominant_emotion,
        "dominant_emotion_confidence": dominant_emotion_confidence,
        "average_confidence": round(avg_conf, 2),
        "total_scenes_detected": len(scenes),
        "label_distribution": label_dist,
        "action_taken": action_taken,
        "has_faces": face_scene_count > 0,
        "face_scene_count": face_scene_count,
        "face_scene_ratio": round(face_scene_count / max(len(scenes), 1), 3),
        "face_sample_hits": face_sample_hits,
        "face_sample_total": face_sample_total,
        "face_sample_ratio": round(face_sample_hits / max(face_sample_total, 1), 3),
    }
    return dominant_label, ai_metadata


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
    _update_task(self.request.id, status="STARTED", progress_step="Generating secure file hash...")
    try:
        with open(video_path_str, "rb") as fh:
            file_hash = hashlib.sha256(fh.read()).hexdigest()
        safe_name = slugify(video_name)
        logger.info(f"File hash for {video_name}: {file_hash[:12]}...")
        
        # ── Smart Edited Detection (Pre-analysis) ──────────────────────────
        heuristic_edited = check_if_edited_by_filename(original_filename) or check_if_edited_by_metadata(video_path_str)
        if heuristic_edited:
            logger.info(f"Heuristics suggest {video_name} is an edited video. Skipping analysis.")
            is_edited_auto = True
        else:
            is_edited_auto = False
            
    except Exception as e:
        logger.error(f"Failed to hash video {video_path_str}: {e}")
        _update_task(self.request.id, status="FAILURE", error_message=str(e), progress_step="error")
        raise e

    # ── Step 2: Process video (pipeline uses the hash-safe public ID) ─────────
    if not is_edited_auto:
        self.update_state(state="PROGRESS", meta={"step": "processing", "message": "Initiating deep video analysis..."})
        _update_task(self.request.id, status="STARTED", progress_step="Initiating deep video analysis...")
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
        _update_task(self.request.id, progress_step="Finalizing analysis and compiling scene index...")
        index_path = os.path.join(base_dir_str, "scene_indexes", f"{video_name}_scene_index.json")
        if not os.path.exists(index_path):
            _update_task(self.request.id, status="FAILURE", error_message="Scene index not generated", progress_step="error")
            return {"status": "error", "message": "Scene index not generated"}

        with open(index_path, "r", encoding="utf-8") as f:
            scenes = json.load(f)

        # ── Step 4: Determine dominant label ─────────────────────────────────────
        dominant_label, ai_metadata = build_ai_metadata_from_scenes(
            scenes,
            video_name=video_name,
        )
    else:
        # ── Heuristic Edited Flow ──────────────────────────────────────────────────
        dominant_label = "edited"
        ai_metadata = {
            "dominant_label": "edited",
            "dominant_emotion": "none",
            "dominant_emotion_confidence": None,
            "average_confidence": 1.0,
            "total_scenes_detected": 1,
            "label_distribution": {"edited": 1},
            "action_taken": "auto_detected_by_heuristics",
            "has_faces": False,
            "face_scene_count": 0,
            "face_scene_ratio": 0.0,
            "face_sample_hits": 0,
            "face_sample_total": 0,
            "face_sample_ratio": 0.0,
        }

    # ── Step 5: Duplicate detection ───────────────────────────────────────────
    col = _get_col()
    existing = col.find_one({"file_hash": file_hash, "status": "organized"})

    # If the existing record was organized under a label we no longer support,
    # ignore the duplicate hit and treat this as a fresh upload so the asset
    # gets re-organized under the current label set.
    VALID_LABELS = {"testimonial", "b-roll", "audience_reaction",
                    "establishing_shot", "other", "edited"}
    if existing and existing.get("dominant_label") not in VALID_LABELS:
        logger.info(
            "Duplicate hit for hash %s... ignored — existing label '%s' is retired. "
            "Re-organizing with fresh classification '%s'.",
            file_hash[:12], existing.get("dominant_label"), dominant_label,
        )
        existing = None

    if existing:
        # Same bytes already organized — skip the re-upload but trust the
        # freshly computed `dominant_label` over whatever is cached on the
        # existing record. The cache can carry stale labels from earlier
        # classifier versions; the new run is the source of truth.
        logger.info(
            "Duplicate detected for hash %s... — reusing existing asset, "
            "label '%s' (cached was '%s')",
            file_hash[:12], dominant_label, existing.get("dominant_label"),
        )
        dup_doc = build_doc(
            original_filename=original_filename,
            file_hash=file_hash,
            cloudinary_public_id=existing["cloudinary_public_id"],
            cloudinary_url=existing["cloudinary_url"],
            dominant_label=dominant_label,
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
            "dominant_label": dominant_label,
            "duplicate_of": str(existing["_id"]),
            "export_path": existing.get("cloudinary_public_id"),
            "ai_metadata": ai_metadata,
        }

    # ── Step 6: Move or Upload video to organized folder ────────────────────────────────
    from services import cloudinary_service
    if not is_edited_auto:
        _update_task(self.request.id, progress_step=f"Organizing video into '{dominant_label}' category...")
        old_pub_id = f"editease/videos/{file_hash}/{safe_name}"
        new_pub_id = f"editease/organized-videos/{dominant_label}/{file_hash}/{safe_name}"
        cloudinary_url, actual_pub_id = cloudinary_service.move_video_returning_id(old_pub_id, new_pub_id)

        if not cloudinary_url:
            # Move failed — log and continue; local file will still be cleaned up
            logger.error(f"Failed to move Cloudinary video for {video_name}")
            actual_pub_id = new_pub_id  # use intended path so record is still useful
    else:
        new_pub_id = f"editease/organized-videos/edited/{file_hash}/{safe_name}"
        self.update_state(state="PROGRESS", meta={"step": "uploading", "message": "Uploading edited video..."})
        _update_task(self.request.id, progress_step="Uploading fully edited video to cloud storage...")
        try:
            cloudinary_url, actual_pub_id = cloudinary_service.upload_video_returning_id(video_path_str, new_pub_id)
        except Exception as e:
            logger.error(f"Failed to upload edited video for {video_name}: {e}")
            _update_task(self.request.id, status="FAILURE", error_message=str(e), progress_step="error")
            raise e

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
        "ai_metadata": ai_metadata,
    }



