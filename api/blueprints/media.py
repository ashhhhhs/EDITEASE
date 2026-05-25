"""Media blueprint: /upload, /export, /thumbnail, /video_clip, /task_status,
/auto_organize, /open_folder, /organized-videos, /organized-videos/download-batch"""
import os
from flask import Blueprint, request, jsonify, send_file, redirect
import cloudinary.api
import cloudinary.utils
import config
from utils.logger import setup_logger
from services import clip_service, task_service, export_service
from api.decorators import login_required, role_required, require_verified_email

logger = setup_logger('media_bp')
media_bp = Blueprint('media', __name__)


def _filter_existing_cloudinary_ids(public_ids: list[str]) -> tuple[list[str], list[str]]:
    """Return (existing_ids, missing_ids) for a list of Cloudinary public IDs.

    Cloudinary's `download_zip_url` fails the entire archive if any of the
    requested IDs is missing. We pre-filter using `resources_by_ids` so a few
    stale MongoDB records (deleted assets / failed uploads) don't break the
    download for everyone else. Cloudinary caps `resources_by_ids` at 100 IDs
    per call so we batch.
    """
    existing: list[str] = []
    BATCH = 100
    for i in range(0, len(public_ids), BATCH):
        chunk = public_ids[i:i + BATCH]
        try:
            res = cloudinary.api.resources_by_ids(chunk, resource_type="video")
            existing.extend(r["public_id"] for r in res.get("resources", []))
        except Exception as exc:
            logger.warning("resources_by_ids failed for chunk: %s", exc)
            # If the lookup itself fails, fall back to including the chunk —
            # better to let Cloudinary fail loudly than to silently drop IDs.
            existing.extend(chunk)
    missing = [pid for pid in public_ids if pid not in set(existing)]
    return existing, missing

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
@require_verified_email
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
@require_verified_email
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
    """Return count of videos per dominant_label.
    Admins see all users. Editors only see their own.
    """
    from flask import g
    from services.organized_video_service import get_label_counts
    user_id = None if g.user.get('role') == 'admin' else g.user.get('id')
    return jsonify(get_label_counts(uploader=user_id))

@media_bp.get('/organized-videos')
@role_required(['admin', 'editor'])
def list_organized_videos():
    """List organized videos with optional filters.
    Admins see all. Editors are scoped to their own uploads.
    Query params: label, from_date, to_date, is_duplicate, search, page, limit
    """
    from flask import g
    from services.organized_video_service import list_organized_videos as svc_list
    is_dup = request.args.get('is_duplicate')
    is_dup_bool = None
    if is_dup is not None:
        is_dup_bool = is_dup.lower() in ('1', 'true', 'yes')
    # Scope to the current user unless they are an admin
    uploader = None if g.user.get('role') == 'admin' else g.user.get('id')
    result = svc_list(
        label=request.args.get('label'),
        from_date=request.args.get('from_date'),
        to_date=request.args.get('to_date'),
        uploader=uploader,
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


@media_bp.delete('/organized-videos')
@role_required(['admin', 'editor'])
@require_verified_email
def delete_organized_videos():
    """Delete selected organized videos.

    Admins can delete any record; editors are scoped to their own uploads.
    """
    from flask import g
    from services.organized_video_service import delete_organized_videos as svc_delete

    data = request.get_json(silent=True) or {}
    result = svc_delete(
        data.get('ids', []),
        requester_id=g.user.get('id'),
        is_admin=g.user.get('role') == 'admin',
    )
    if 'error' in result:
        return jsonify(result), result.get('status', 400)
    return jsonify(result)


@media_bp.get('/organized-videos/logs')
@role_required(['admin', 'editor'])
def get_organized_video_logs():
    """Return processing logs for organized videos.
    Links organized_videos → tasks via batch_id.
    Query params: label, page, limit, search
    """
    from services.organized_video_service import get_processing_logs
    result = get_processing_logs(
        label=request.args.get('label'),
        search=request.args.get('search'),
        page=request.args.get('page', 1, type=int),
        limit=request.args.get('limit', 30, type=int),
    )
    return jsonify(result)


@media_bp.post('/organized-videos/download')
@role_required(['admin', 'editor'])
@require_verified_email
def download_organized_video():
    """Generate a signed Cloudinary URL with the attachment flag for direct download."""
    from services.organized_video_service import get_organized_video as svc_get
    data = request.get_json(force=True) or {}
    video_id = data.get('id')
    if not video_id:
        return jsonify({'error': 'id is required'}), 400
    doc = svc_get(video_id)
    if not doc:
        return jsonify({'error': 'Not found'}), 404
        
    pid = doc.get('cloudinary_public_id')
    if not pid:
        return jsonify({'error': 'No cloud asset available'}), 404
        
    # Generate URL with fl_attachment to force browser "Save As"
    download_url = cloudinary.utils.cloudinary_url(
        pid,
        resource_type="video",
        flags="attachment",
        attachment=doc.get('download_name', 'video.mp4')
    )[0]
    
    return jsonify({'url': download_url})


# ── Batch ZIP (background job) ───────────────────────────────────────────────

@media_bp.post('/organized-videos/download-batch')
@role_required(['admin', 'editor'])
@require_verified_email
def start_batch_download():
    """Generate an instant, signed Cloudinary ZIP URL for selected videos."""
    from flask import g
    from bson import ObjectId
    from services.organized_video_service import _get_col, validate_batch_request
    data = request.get_json(force=True) or {}
    ids = data.get('ids', [])
    ok, err = validate_batch_request(ids)
    if not ok:
        return jsonify({'error': err}), 400
    
    col = _get_col()
    # Build ownership filter — admins can download any video
    ownership_filter = {"_id": {"$in": [ObjectId(i) for i in ids if ObjectId.is_valid(i)]}}
    if g.user.get('role') != 'admin':
        ownership_filter["uploaded_by"] = g.user.get('id')
    docs = list(col.find(ownership_filter))
    if not docs:
        return jsonify({'error': 'No valid videos found (or access denied)'}), 404
        
    public_ids = [doc.get('cloudinary_public_id') for doc in docs if doc.get('cloudinary_public_id')]
    if not public_ids:
        return jsonify({'error': 'No cloud assets found for these videos'}), 404

    existing_ids, missing_ids = _filter_existing_cloudinary_ids(public_ids)
    if missing_ids:
        logger.warning(
            "Skipping %d missing Cloudinary asset(s) in download-batch: %s",
            len(missing_ids), missing_ids,
        )
    if not existing_ids:
        return jsonify({'error': 'All requested cloud assets are missing'}), 404

    # Generate the signed Cloudinary ZIP URL (expires in 1 hour)
    zip_url = cloudinary.utils.download_zip_url(
        public_ids=existing_ids,
        resource_type="video",
        flatten_folders=True,
    )

    msg = f'Instant ZIP created for {len(existing_ids)} files'
    if missing_ids:
        msg += f' ({len(missing_ids)} unavailable were skipped)'
    return jsonify({
        'status': 'SUCCESS',
        'url': zip_url,
        'message': msg,
        'skipped': len(missing_ids),
    })


@media_bp.post('/organized-videos/download-category')
@role_required(['admin', 'editor'])
@require_verified_email
def download_category():
    """Generate a signed Cloudinary ZIP URL for ALL videos in a category.
    Non-admins are scoped to their own uploads. Capped at 50 files.
    """
    from flask import g
    from services.organized_video_service import _get_col
    data = request.get_json(force=True) or {}
    label = data.get('label', '').strip()
    if not label:
        return jsonify({'error': 'label is required'}), 400

    col = _get_col()
    query = {"dominant_label": label, "status": "organized"}
    if g.user.get('role') != 'admin':
        query["uploaded_by"] = g.user.get('id')

    CAP = 50
    docs = list(col.find(query, {"cloudinary_public_id": 1}).limit(CAP))
    if not docs:
        return jsonify({'error': 'No videos found in this category'}), 404

    public_ids = [d['cloudinary_public_id'] for d in docs if d.get('cloudinary_public_id')]
    if not public_ids:
        return jsonify({'error': 'No cloud assets found for this category'}), 404

    existing_ids, missing_ids = _filter_existing_cloudinary_ids(public_ids)
    if missing_ids:
        logger.warning(
            "Skipping %d missing Cloudinary asset(s) in download-category '%s': %s",
            len(missing_ids), label, missing_ids,
        )
    if not existing_ids:
        return jsonify({'error': 'All cloud assets for this category are missing'}), 404

    zip_url = cloudinary.utils.download_zip_url(
        public_ids=existing_ids,
        resource_type="video",
        flatten_folders=True,
    )
    capped = len(docs) == CAP
    msg = f'ZIP ready for {len(existing_ids)} files'
    if capped:
        msg += ' (first 50 only)'
    if missing_ids:
        msg += f' ({len(missing_ids)} unavailable were skipped)'
    return jsonify({
        'status': 'SUCCESS',
        'url': zip_url,
        'count': len(existing_ids),
        'capped': capped,
        'skipped': len(missing_ids),
        'message': msg,
    })
