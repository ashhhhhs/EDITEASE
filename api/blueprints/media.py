"""Media blueprint: /upload, /export, /thumbnail, /video_clip, /task_status, /auto_organize, /open_folder"""
import os
from flask import Blueprint, request, jsonify, send_file
import config
from utils.logger import setup_logger
from services import clip_service, task_service, export_service
from api.decorators import login_required, role_required, require_verified_email

logger = setup_logger('media_bp')
media_bp = Blueprint('media', __name__)

@media_bp.get('/thumbnail/<clip_id>')
def serve_thumbnail(clip_id):
    path = clip_service.resolve_thumbnail(clip_id)
    if not path:
        return jsonify({'error': 'file not found'}), 404
    return send_file(path, mimetype='image/jpeg')

@media_bp.get('/video_clip/<clip_id>')
def serve_video_clip(clip_id):
    path = clip_service.resolve_video_path(clip_id)
    if not path:
        return jsonify({'error': 'file not found'}), 404
    return send_file(path, mimetype='video/mp4')

@media_bp.get('/task_status/<task_id>')
@login_required
def get_task_status(task_id):
    return jsonify(task_service.get_task_status(task_id))

@media_bp.post('/upload')
@role_required(['admin', 'editor'])
def upload_video():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    file_path = config.DATA_DIR / file.filename
    file.save(str(file_path))
    logger.info(f'Video uploaded to {file_path}')
    task = task_service.dispatch_process(str(file_path))
    return jsonify({'status': 'uploaded', 'message': 'Processing started', 'video_path': str(file_path), 'task_id': task.id})

@media_bp.post('/auto_organize')
@role_required(['admin', 'editor'])
def auto_organize():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    file_path = config.DATA_DIR / file.filename
    file.save(str(file_path))
    logger.info(f'Auto-organize upload: {file_path}')
    task = task_service.dispatch_auto_organize(str(file_path))
    return jsonify({'status': 'uploaded', 'message': 'Auto-organize started', 'video_path': str(file_path), 'task_id': task.id})

@media_bp.post('/export')
@role_required(['admin', 'editor'])
@require_verified_email
def export_scene():
    data = request.get_json(force=True) or {}
    res = export_service.export_single_clip(data.get('video'), data.get('scene_id'))
    return jsonify(res) if 'error' not in res else (jsonify(res), 400)

@media_bp.post('/export_batch')
@role_required(['admin', 'editor'])
@require_verified_email
def export_batch():
    return jsonify(export_service.export_batch(request.get_json(force=True) or {}))

@media_bp.post('/open_folder')
@role_required(['admin'])
def open_folder():
    data = request.get_json(force=True) or {}
    path = data.get('path')
    if not path or not os.path.exists(path):
        return jsonify({'error': 'invalid path'}), 400
    if os.name == 'nt':
        os.startfile(path)
    return jsonify({'ok': True, 'opened': path})
