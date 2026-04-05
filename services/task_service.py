import os

import config
from api.celery_worker import celery_app, process_video_task, auto_organize_task
from utils.logger import setup_logger
from pymongo import MongoClient
import datetime

logger = setup_logger("task_service")

client = MongoClient(config.MONGO_URI)
db = client[config.DB_NAME]
tasks_col = db["tasks"]

def insert_task_record(task_id, task_type, initiated_by=None, input_path=None):
    now = datetime.datetime.utcnow().isoformat()
    doc = {
        "task_id": task_id,
        "type": task_type,
        "status": "PENDING",
        "created_at": now,
        "updated_at": now,
        "initiated_by": initiated_by,
        "input_path": input_path,
        "output_path": None,
        "error_message": None,
        "progress_step": "Queued"
    }
    tasks_col.insert_one(doc)

def update_task_record(task_id, **kwargs):
    kwargs["updated_at"] = datetime.datetime.utcnow().isoformat()
    tasks_col.update_one({"task_id": task_id}, {"$set": kwargs})

def dispatch_process(file_path, user_id=None):
    """Dispatch standard process_video task."""
    task = process_video_task.delay(file_path, str(config.BASE_DIR))
    insert_task_record(task.id, "upload", initiated_by=user_id, input_path=file_path)
    logger.info(f"Dispatched process task {task.id} for {file_path}")
    return task

def dispatch_auto_organize(file_path, user_id=None):
    """Dispatch auto_organize task."""
    task = auto_organize_task.delay(file_path, str(config.BASE_DIR), user_id)
    insert_task_record(task.id, "auto_organize", initiated_by=user_id, input_path=file_path)
    logger.info(f"Dispatched auto-organize task {task.id} for {file_path}")
    return task

def get_task_status(task_id):
    """Query celery worker for task status."""
    task_result = celery_app.AsyncResult(task_id)
    
    if task_result.ready():
        result_data = task_result.result
    else:
        # info holds the meta dictionary during PROGRESS
        result_data = task_result.info

    # If info is just a string (sometimes Celery does this depending on backend), wrap it
    if isinstance(result_data, str):
        result_data = {"message": result_data}

    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": result_data
    }

def get_paginated_jobs(page=1, limit=20, status=None, task_type=None):
    page = max(1, int(page))
    limit = max(1, min(int(limit), 200))
    skip = (page - 1) * limit
    
    q = {}
    if status: q["status"] = status
    if task_type: q["type"] = task_type
    
    cursor = tasks_col.find(q).sort("created_at", -1).skip(skip).limit(limit)
    jobs = []
    for j in cursor:
        j["_id"] = str(j["_id"])
        jobs.append(j)
    total = tasks_col.count_documents(q)
    return {"jobs": jobs, "total": total, "page": page, "limit": limit}

def get_job_by_task_id(task_id):
    job = tasks_col.find_one({"task_id": task_id})
    if job:
        job["_id"] = str(job["_id"])
    return job
