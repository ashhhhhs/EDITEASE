import os
from flask import Flask, request, jsonify, send_file, g
from flask_cors import CORS
from flasgger import Swagger

import config
from utils.logger import setup_logger

from services import clip_service
from services import task_service
from services import export_service
from services import auth_service
from functools import wraps

logger = setup_logger("api_server")

app = Flask(__name__)
CORS(app)
swagger = Swagger(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token = token.split(" ")[1]
        
        user = auth_service.get_user_by_token(token)
        if not user:
            return jsonify({"error": "Unauthorized", "status": 401}), 401
            
        g.user = user
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get("Authorization")
            if token and token.startswith("Bearer "):
                token = token.split(" ")[1]
            
            user = auth_service.get_user_by_token(token)
            if not user:
                return jsonify({"error": "Unauthorized", "status": 401}), 401
                
            if user.get("role") not in allowed_roles:
                return jsonify({"error": "Forbidden: insufficient role", "status": 403}), 403
                
            g.user = user
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.post("/register")
def register():
    data = request.get_json(force=True) or {}
    username = data.get("username")
    password = data.get("password")
    name = data.get("name")
    email = data.get("email")
    
    res = auth_service.register_user(username, password, name, email)
    if "error" in res:
        return jsonify(res), res.get("status", 400)
    return jsonify(res)

@app.post("/login")
def login():
    data = request.get_json(force=True) or {}
    username = data.get("username")
    password = data.get("password")
    
    res = auth_service.login_user(username, password)
    if "error" in res:
        return jsonify(res), res.get("status", 401)
    return jsonify(res)

@app.post("/logout")
@login_required
def logout():
    token = request.headers.get("Authorization").split(" ")[1]
    res = auth_service.logout_user(token)
    return jsonify(res)

@app.get("/me")
@login_required
def get_me():
    return jsonify({"user": g.user})

@app.get("/health")
def health():
    return jsonify({"ok": True, "db": config.DB_NAME, "collection": config.COLLECTION})

@app.get("/thumbnail/<clip_id>")
def serve_thumbnail(clip_id):
    """
    Serve a thumbnail image from the local filesystem by MongoDB _id.
    ---
    responses:
      200:
        description: The thumbnail image
    """
    path = clip_service.resolve_thumbnail(clip_id)
    if not path:
        return jsonify({"error": "file not found"}), 404
    return send_file(path, mimetype="image/jpeg")

@app.get("/video_clip/<clip_id>")
def serve_video_clip(clip_id):
    """
    Serve a video clip for preview by MongoDB _id.
    ---
    responses:
      200:
        description: The video file
    """
    path = clip_service.resolve_video_path(clip_id)
    if not path:
        return jsonify({"error": "file not found"}), 404
    return send_file(path, mimetype="video/mp4")

@app.get("/search")
@role_required(["admin", "reviewer", "editor"])
def search():
    filters = {
        "scene_label": request.args.get("scene_label"),
        "emotion": request.args.get("emotion"),
        "video": request.args.get("video"),
        "reviewed": request.args.get("reviewed"),
        "uncertain": request.args.get("uncertain"),
        "min_duration": request.args.get("min_duration"),
        "max_duration": request.args.get("max_duration"),
        "page": request.args.get("page", 1, type=int)
    }
    filters = {k: v for k, v in filters.items() if v is not None}
    limit = request.args.get("limit", 100, type=int)
    results = clip_service.search_clips(filters, limit=limit)
    return jsonify(results)

@app.post("/update_scene")
@role_required(['admin', 'reviewer'])
def update_scene():
    """
    JSON body:
    {
      "video": "C3631",
      "scene_id": 1,
      "scene_label": "testimonial",
      "dominant_emotion_overall": "happy",
      "reviewed": true,
      "notes": "optional text",
      "manual_scene_label": "testimonial",
      "manual_emotion": "happy"
    }
    """
    data = request.get_json(force=True) or {}
    video = data.get("video")
    scene_id = data.get("scene_id")
    
    res = clip_service.update_clip(video, scene_id, data)
    if "error" in res:
        status = 404 if "not found" in res["error"] else 400
        return jsonify(res), status
    return jsonify(res)

@app.post("/export")
@role_required(['admin', 'editor'])
def export_scene():
    data = request.get_json(force=True) or {}
    video = data.get("video")
    scene_id = data.get("scene_id")
    
    res = export_service.export_single_clip(video, scene_id)
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res)

@app.post("/export_batch")
@role_required(['admin', 'editor'])
def export_batch():
    filters = request.get_json(force=True) or {}
    res = export_service.export_batch(filters)
    return jsonify(res)

@app.post("/upload")
@role_required(['admin', 'editor'])
def upload_video():
    """
    Upload a video which will be processed by Celery in the background.
    ---
    parameters:
      - name: file
        in: formData
        type: file
        required: true
    responses:
      200:
        description: Returns a task_id to poll for status
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    file_path = config.DATA_DIR / file.filename
    file.save(str(file_path))
    logger.info(f"Video uploaded to {file_path}")
    
    task = task_service.dispatch_process(str(file_path))
    return jsonify({
        "status": "uploaded", 
        "message": "Processing started in background", 
        "video_path": str(file_path),
        "task_id": task.id
    })

@app.get("/task_status/<task_id>")
@login_required
def get_task_status(task_id):
    return jsonify(task_service.get_task_status(task_id))

@app.post("/auto_organize")
@role_required(['admin', 'editor'])
def auto_organize():
    """
    One-click Editor mode: upload → process → export organized clips.
    ---
    parameters:
      - name: file
        in: formData
        type: file
        required: true
    responses:
      200:
        description: Returns task_id to poll for organized results
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    file_path = config.DATA_DIR / file.filename
    file.save(str(file_path))
    logger.info(f"Auto-organize upload: {file_path}")
    
    task = task_service.dispatch_auto_organize(str(file_path))
    return jsonify({
        "status": "uploaded",
        "message": "Auto-organize started",
        "video_path": str(file_path),
        "task_id": task.id
    })

@app.post("/open_folder")
@role_required(['admin'])
def open_folder():
    """Opens a local folder strictly for testing on Windows. Remove in prod."""
    data = request.get_json(force=True) or {}
    path = data.get("path")
    if not path or not os.path.exists(path):
        return jsonify({"error": "invalid path"}), 400
    os.startfile(path)
    return jsonify({"ok": True, "opened": path})

# --- Phase 3 Admin & Operational Endpoints ---

@app.get("/admin/overview")
@role_required(["admin"])
def admin_overview():
    total_users = auth_service.users_col.count_documents({})
    active_users = auth_service.users_col.count_documents({"is_active": True})
    
    total_videos = len(clip_service.col.distinct("video"))
    total_clips = clip_service.col.count_documents({})
    
    pending_review = clip_service.col.count_documents({"reviewed": False})
    uncertain_clips = clip_service.col.count_documents({"uncertain": True})
    
    from services.task_service import tasks_col
    tasks_running = tasks_col.count_documents({"status": {"$in": ["PENDING", "STARTED"]}})
    tasks_failed = tasks_col.count_documents({"status": "FAILURE"})
    
    return jsonify({
        "total_users": total_users,
        "active_users": active_users,
        "total_videos": total_videos,
        "total_clips": total_clips,
        "pending_review": pending_review,
        "uncertain_clips": uncertain_clips,
        "tasks_running": tasks_running,
        "tasks_failed": tasks_failed
    })

@app.get("/admin/users")
@role_required(["admin"])
def get_users():
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    return jsonify(auth_service.get_paginated_users(page, limit))

@app.patch("/admin/users/<target_id>/role")
@role_required(["admin"])
def update_user_role_ep(target_id):
    data = request.get_json(force=True) or {}
    new_role = data.get("role")
    if new_role not in ["admin", "editor", "reviewer"]:
        return jsonify({"error": "Invalid role"}), 400
    
    res = auth_service.update_user_role(target_id, new_role, str(g.user["id"]))
    if "error" in res:
        return jsonify(res), res.get("status", 400)
    return jsonify(res)

@app.patch("/admin/users/<target_id>/status")
@role_required(["admin"])
def update_user_status_ep(target_id):
    data = request.get_json(force=True) or {}
    is_active = data.get("is_active")
    if is_active is None:
        return jsonify({"error": "is_active boolean required"}), 400
    
    res = auth_service.update_user_status(target_id, bool(is_active), str(g.user["id"]))
    if "error" in res:
        return jsonify(res), res.get("status", 400)
    return jsonify(res)

@app.get("/admin/jobs")
@role_required(["admin"])
def get_jobs():
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    status_filter = request.args.get("status")
    type_filter = request.args.get("type")
    
    from services.task_service import get_paginated_jobs
    return jsonify(get_paginated_jobs(page, limit, status_filter, type_filter))

@app.get("/admin/jobs/<task_id>")
@role_required(["admin"])
def get_job_detail_ep(task_id):
    from services.task_service import get_job_by_task_id
    job = get_job_by_task_id(task_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)

@app.post("/review/bulk-update")
@role_required(["admin", "reviewer"])
def bulk_update_ep():
    data = request.get_json(force=True) or {}
    keys = data.get("scene_keys", [])
    update_data = data.get("update_data", {})
    
    if not keys or not update_data:
        return jsonify({"error": "scene_keys and update_data required"}), 400
        
    return jsonify(clip_service.bulk_update_clips(keys, update_data))
if __name__ == "__main__":
    app.run(host=config.API_HOST, port=config.API_PORT, debug=config.API_DEBUG)
