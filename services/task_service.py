import os

import config
from api.celery_worker import celery_app, process_video_task, auto_organize_task
from utils.logger import setup_logger

logger = setup_logger("task_service")

def dispatch_process(file_path):
    """Dispatch standard process_video task."""
    task = process_video_task.delay(file_path, str(config.BASE_DIR))
    logger.info(f"Dispatched process task {task.id} for {file_path}")
    return task

def dispatch_auto_organize(file_path):
    """Dispatch auto_organize task."""
    task = auto_organize_task.delay(file_path, str(config.BASE_DIR))
    logger.info(f"Dispatched auto-organize task {task.id} for {file_path}")
    return task

def get_task_status(task_id):
    """Query celery worker for task status."""
    task_result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }
