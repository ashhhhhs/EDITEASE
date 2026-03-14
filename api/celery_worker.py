import os
from celery import Celery

import config
from utils.logger import setup_logger

logger = setup_logger("celery_worker")

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
    
    try:
        # In a more advanced setup, you'd report progress back to celery
        # self.update_state(state='PROGRESS', meta={'current': 10, 'total': 100})
        process_video(video_path_str, base_dir_str)
        logger.info(f"Finished Celery task for video: {video_path_str}")
        return {"status": "success", "video_path": video_path_str}
    except Exception as e:
        logger.error(f"Celery task failed for {video_path_str}: {e}", exc_info=True)
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
    from pipeline.processing.run_pipeline import process_video
    try:
        process_video(video_path_str, base_dir_str)
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        raise e
    
    # Step 2: Read the generated scene index
    self.update_state(state='PROGRESS', meta={'step': 'exporting', 'message': 'Organizing clips...'})
    index_path = os.path.join(base_dir_str, "scene_indexes", f"{video_name}_scene_index.json")
    if not os.path.exists(index_path):
        return {"status": "error", "message": "Scene index not generated"}
    
    with open(index_path, "r", encoding="utf-8") as f:
        scenes = json.load(f)
    
    # Step 3: Calculate dominant scene label and copy full video
    from collections import Counter
    import shutil
    
    labels = [scene.get("scene_label", "other") or "other" for scene in scenes]
    dominant_label = "other"
    if labels:
        counts = Counter(labels)
        dominant_label = counts.most_common(1)[0][0]
        
    exports_dir = Path(base_dir_str) / "exports"
    out_dir = exports_dir / dominant_label
    out_dir.mkdir(parents=True, exist_ok=True)
    
    original_ext = os.path.splitext(video_path_str)[1] or ".mp4"
    out_name = f"{video_name}_full{original_ext}"
    out_path = out_dir / out_name
    
    try:
        shutil.copy2(video_path_str, out_path)
        logger.info(f"Auto-organize: Copied full video {video_name} to {out_path}")
    except Exception as e:
        logger.error(f"Copy failed for {video_name}: {e}")
        return {"status": "error", "message": "Failed to copy video"}
    
    return {
        "status": "success",
        "video": video_name,
        "dominant_label": dominant_label,
        "export_path": str(out_path)
    }
