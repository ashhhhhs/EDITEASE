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
        process_video(video_path_str, base_dir_str)
        logger.info(f"Finished Celery task for video: {video_path_str}")
        _update_task(self.request.id, status="SUCCESS", progress_step="done")
        return {"status": "success", "video_path": video_path_str}
    except Exception as e:
        logger.error(f"Celery task failed for {video_path_str}: {e}", exc_info=True)
        _update_task(self.request.id, status="FAILURE", error_message=str(e), progress_step="error")
        raise e


@celery_app.task(bind=True, name="auto_organize_task")
def auto_organize_task(self, video_path_str: str, base_dir_str: str):
    """
    One-click auto-organize: process video → copy full video into dominant scene type folder.
    This is the Editor mode flow.
    """
    import json
    from pathlib import Path
    
    video_name = os.path.splitext(os.path.basename(video_path_str))[0]
    logger.info(f"Auto-organize started for: {video_name}")
    
    # Step 1: Process video (detect scenes, classify, etc.)
    self.update_state(state='PROGRESS', meta={'step': 'processing', 'message': 'Analyzing video...'})
    _update_task(self.request.id, status="STARTED", progress_step="processing")
    from pipeline.processing.run_pipeline import process_video
    try:
        process_video(video_path_str, base_dir_str)
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        _update_task(self.request.id, status="FAILURE", error_message=str(e), progress_step="error")
        raise e
    
    # Step 2: Read the generated scene index
    self.update_state(state='PROGRESS', meta={'step': 'exporting', 'message': 'Organizing clips...'})
    _update_task(self.request.id, progress_step="exporting")
    index_path = os.path.join(base_dir_str, "scene_indexes", f"{video_name}_scene_index.json")
    if not os.path.exists(index_path):
        _update_task(self.request.id, status="FAILURE", error_message="Scene index not generated", progress_step="error")
        return {"status": "error", "message": "Scene index not generated"}
    
    with open(index_path, "r", encoding="utf-8") as f:
        scenes = json.load(f)
    
    # Step 3: Calculate dominant scene label and copy full video
    from collections import Counter
    import shutil
    
    confident_labels = [scene.get("scene_label", "other") for scene in scenes if scene.get("reviewed") is True]
    if not confident_labels:
        confident_labels = [scene.get("scene_label", "other") for scene in scenes]
        
    dominant_label = "other"
    if confident_labels:
        counts = Counter(confident_labels)
        dominant_label = counts.most_common(1)[0][0]
        
    try:
        from services import cloudinary_service
        old_pub_id = f"editease/videos/{video_name}"
        new_pub_id = f"editease/exports/{dominant_label}/{video_name}"
        cloudinary_service.move_video(old_pub_id, new_pub_id)
    except Exception as e:
        logger.error(f"Failed to move Cloudinary video for {video_name}: {e}")
        
    # Remove original video from local storage
    try:
        if os.path.exists(video_path_str):
            os.remove(video_path_str)
            logger.info("Removed original video from local storage: %s", video_path_str)
    except Exception as e:
        logger.warning("Failed to remove original video %s: %s", video_path_str, e)
        
    _update_task(self.request.id, status="SUCCESS", progress_step="done", output_path=new_pub_id)
    return {
        "status": "success",
        "video": video_name,
        "dominant_label": dominant_label,
        "export_path": new_pub_id
    }
