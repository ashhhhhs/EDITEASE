"""Media blueprint: /upload, /export, /thumbnail, /video_clip, /task_status,
/auto_organize, /open_folder, /organized-videos, /organized-videos/download-batch"""
import os
from flask import Blueprint, request, jsonify, send_file, redirect
import config
from utils.logger import setup_logger
from services import clip_service, task_service, export_service
from api.decorators import login_required, role_required, require_verified_email

logger = setup_logger('media_bp')
media_bp = Blueprint('media', __name__)

@media_bp.get('/thumbnail/<clip_id>')
def serve_thumbnail(clip_id):
    url_or_path = clip_service.resolve_thumbnail(clip_id)
    if not url_or_path:
        return jsonify({'error': 'file not found'}), 404
    # Cloudinary URL → redirect; local path → send_file
    if url_or_path.startswith('http'):
        return redirect(url_or_path, code=302)
    return send_file(url_or_path, mimetype='image/jpeg')

@media_bp.get('/video_clip/<clip_id>')
def serve_video_clip(clip_id):
    url_or_path = clip_service.resolve_video_path(clip_id)
    if not url_or_path:
        return jsonify({'error': 'file not found'}), 404
    # Cloudinary URL → redirect; local path → send_file
    if url_or_path.startswith('http'):
        return redirect(url_or_path, code=302)
    return send_file(url_or_path, mimetype='video/mp4')

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
    logger.info(f'Video saved locally to {file_path}')
    task = task_service.dispatch_process(str(file_path))
    return jsonify({'status': 'uploaded', 'message': 'Processing started', 'video_path': str(file_path), 'task_id': task.id})

@media_bp.post('/auto_organize')
@role_required(['admin', 'editor'])
def auto_organize():
    from flask import g
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    file_path = config.DATA_DIR / file.filename
    file.save(str(file_path))
    logger.info(f'Auto-organize upload saved locally: {file_path}')
    user_id = str(g.user['id']) if g.user else None
    task = task_service.dispatch_auto_organize(str(file_path), user_id=user_id)
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


# ── Organized Videos ────────────────────────────────────────────────────────

@media_bp.get('/organized-videos/stats')
@role_required(['admin', 'editor'])
def get_organized_video_stats():
    """Return count of videos per dominant_label."""
    from services.organized_video_service import get_label_counts
    return jsonify(get_label_counts())

@media_bp.get('/organized-videos')
@role_required(['admin', 'editor'])
def list_organized_videos():
    """List organized videos with optional filters.
    Query params: label, from_date, to_date, uploader, is_duplicate, search, page, limit
    """
    from services.organized_video_service import list_organized_videos as svc_list
    is_dup = request.args.get('is_duplicate')
    is_dup_bool = None
    if is_dup is not None:
        is_dup_bool = is_dup.lower() in ('1', 'true', 'yes')
    result = svc_list(
        label=request.args.get('label'),
        from_date=request.args.get('from_date'),
        to_date=request.args.get('to_date'),
        uploader=request.args.get('uploader'),
        is_duplicate=is_dup_bool,
        search=request.args.get('search'),
        page=request.args.get('page', 1, type=int),
        limit=request.args.get('limit', 20, type=int),
    )
    return jsonify(result)


@media_bp.get('/organized-videos/<video_id>')
@role_required(['admin', 'editor'])
def get_organized_video(video_id):
    """Fetch a single organized video record by ID."""
    from services.organized_video_service import get_organized_video as svc_get
    doc = svc_get(video_id)
    if not doc:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(doc)


@media_bp.post('/organized-videos/download')
@role_required(['admin', 'editor'])
@require_verified_email
def download_organized_video():
    """Redirect to the Cloudinary URL for a single organized video."""
    from services.organized_video_service import get_organized_video as svc_get
    data = request.get_json(force=True) or {}
    video_id = data.get('id')
    if not video_id:
        return jsonify({'error': 'id is required'}), 400
    doc = svc_get(video_id)
    if not doc:
        return jsonify({'error': 'Not found'}), 404
    url = doc.get('cloudinary_url')
    if not url:
        return jsonify({'error': 'No Cloudinary URL available for this video'}), 404
    return redirect(url, code=302)


# ── Batch ZIP (background job) ───────────────────────────────────────────────

@media_bp.post('/organized-videos/download-batch')
@role_required(['admin', 'editor'])
@require_verified_email
def start_batch_download():
    """Enqueue a background ZIP build for selected organized videos.
    Body: { "ids": ["<id1>", "<id2>", ...] }  (max 10)
    Returns: { "task_id": "..." }
    """
    from flask import g
    from services.organized_video_service import validate_batch_request
    from api.celery_worker import build_zip_task
    data = request.get_json(force=True) or {}
    ids = data.get('ids', [])
    ok, err = validate_batch_request(ids)
    if not ok:
        return jsonify({'error': err}), 400
    user_id = str(g.user['id']) if g.user else None
    task = build_zip_task.delay(ids, user_id)
    return jsonify({'task_id': task.id, 'status': 'queued'})


@media_bp.get('/organized-videos/download-batch/<task_id>')
@role_required(['admin', 'editor'])
def poll_batch_download(task_id):
    """Poll the status of a batch ZIP job.
    Returns status; streams the ZIP file when status == SUCCESS.
    """
    import os
    from services.task_service import tasks_col
    from services.organized_video_service import get_zip_download_path
    job = tasks_col.find_one({'task_id': task_id, 'type': 'build_zip'})
    if not job:
        return jsonify({'error': 'Task not found'}), 404
    status = job.get('status')
    if status == 'SUCCESS':
        zip_path = get_zip_download_path(task_id)
        if not zip_path or not os.path.exists(zip_path):
            return jsonify({'error': 'ZIP file not found on server'}), 404
        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name='organized-videos.zip',
        )
    if status == 'FAILURE':
        return jsonify({'status': 'FAILURE', 'error': job.get('error_message', 'Unknown error')}), 500
    return jsonify({'status': status, 'progress_step': job.get('progress_step')})
