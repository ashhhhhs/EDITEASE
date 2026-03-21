"""Review blueprint: /search, /update_scene, /review/bulk-update"""
from flask import Blueprint, request, jsonify
from services import clip_service
from api.decorators import role_required

review_bp = Blueprint('review', __name__)

@review_bp.get('/search')
@role_required(['admin', 'reviewer', 'editor'])
def search():
    filters = {k: request.args.get(k) for k in ['scene_label', 'emotion', 'video', 'reviewed', 'uncertain', 'min_duration', 'max_duration']}
    filters['page'] = request.args.get('page', 1, type=int)
    filters = {k: v for k, v in filters.items() if v is not None}
    limit = request.args.get('limit', 100, type=int)
    return jsonify(clip_service.search_clips(filters, limit=limit))

@review_bp.post('/update_scene')
@role_required(['admin', 'reviewer'])
def update_scene():
    data = request.get_json(force=True) or {}
    video = data.get('video')
    scene_id = data.get('scene_id')
    res = clip_service.update_clip(video, scene_id, data)
    if 'error' in res:
        return jsonify(res), 404 if 'not found' in res['error'] else 400
    return jsonify(res)

@review_bp.post('/review/bulk-update')
@role_required(['admin', 'reviewer'])
def bulk_update_ep():
    data = request.get_json(force=True) or {}
    keys = data.get('scene_keys', [])
    update_data = data.get('update_data', {})
    if not keys or not update_data:
        return jsonify({'error': 'scene_keys and update_data required'}), 400
    return jsonify(clip_service.bulk_update_clips(keys, update_data))
