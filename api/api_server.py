import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flasgger import Swagger

import config
from utils.logger import setup_logger

from services import clip_service
from services import task_service
from services import export_service

logger = setup_logger("api_server")

app = Flask(__name__)
CORS(app)
swagger = Swagger(app)

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
def search_scenes():
    """
    Search and filter scenes in the database.
    ---
    responses:
      200:
        description: A list of scenes matching the filters
    """
    limit = request.args.get("limit", 100)
    filters = request.args.to_dict()
    res = clip_service.search_clips(filters, limit)
    return jsonify(res)

@app.post("/update_scene")
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
def export_scene():
    data = request.get_json(force=True) or {}
    video = data.get("video")
    scene_id = data.get("scene_id")
    
    res = export_service.export_single_clip(video, scene_id)
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res)

@app.post("/export_batch")
def export_batch():
    filters = request.get_json(force=True) or {}
    res = export_service.export_batch(filters)
    return jsonify(res)

@app.post("/upload")
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
def get_task_status(task_id):
    return jsonify(task_service.get_task_status(task_id))

@app.post("/auto_organize")
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
def open_folder():
    """Open a local folder in the system file explorer. [Desktop Only]
    ---
    parameters:
      - name: path
        in: body
        type: string
        required: true
    responses:
      200:
        description: Folder opened
    """
    data = request.get_json(force=True)
    folder_path = data.get("path", "")
    
    res = export_service.open_local_folder(folder_path)
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res)

if __name__ == "__main__":
    app.run(host=config.API_HOST, port=config.API_PORT, debug=config.API_DEBUG)
