"""Review blueprint: /search, /review/bulk-update"""
from flask import Blueprint, request, jsonify, g
from services import clip_service
from api.decorators import role_required

review_bp = Blueprint('review', __name__)

@review_bp.get('/review/assignees')
@role_required(['admin', 'editor'])
def review_assignees():
    from services.auth_service import get_review_assignees
    return jsonify({"users": get_review_assignees(exclude_user_id=g.user.get('id'))})


@review_bp.get('/search')
@role_required(['admin', 'editor', 'reviewer'])
def search():
    filters = {k: request.args.get(k) for k in ['scene_label', 'emotion', 'video', 'reviewed', 'uncertain', 'review_request_status', 'assigned_to_me', 'requested_by_me', 'resolution_unseen', 'min_duration', 'max_duration']}
    filters['page'] = request.args.get('page', 1, type=int)
    filters = {k: v for k, v in filters.items() if v is not None}
    limit = request.args.get('limit', 100, type=int)
    return jsonify(clip_service.search_clips(filters, limit=limit, current_user=g.user))

@review_bp.post('/review/bulk-update')
@role_required(['admin', 'editor', 'reviewer'])
def bulk_update_ep():
    data = request.get_json(force=True) or {}
    keys = data.get('scene_keys', [])
    update_data = data.get('update_data', {})
    if not keys or not update_data:
        return jsonify({'error': 'scene_keys and update_data required'}), 400
    return jsonify(clip_service.bulk_update_clips(keys, update_data, current_user=g.user))


@review_bp.post('/review/request-admin')
@role_required(['editor', 'reviewer'])
def request_admin_review_ep():
    data = request.get_json(force=True) or {}
    res = clip_service.request_admin_review(
        data.get('scene_keys', []),
        data.get('reason', ''),
        current_user=g.user,
    )
    if 'error' in res:
        return jsonify(res), res.get('status', 400)
    return jsonify(res)


@review_bp.post('/review/request-peer')
@role_required(['editor'])
def request_peer_review_ep():
    from services.auth_service import get_user_by_id

    data = request.get_json(force=True) or {}
    assignee = get_user_by_id(data.get('assignee_id'))
    if not assignee:
        return jsonify({'error': 'Assignee not found'}), 404

    res = clip_service.request_peer_review(
        data.get('scene_keys', []),
        assignee,
        data.get('reason', ''),
        current_user=g.user,
    )
    if 'error' in res:
        return jsonify(res), res.get('status', 400)
    return jsonify(res)


@review_bp.post('/review/requests/resolve')
@role_required(['admin'])
def resolve_review_requests_ep():
    data = request.get_json(force=True) or {}
    res = clip_service.resolve_review_requests(
        data.get('scene_keys', []),
        data.get('status', ''),
        data.get('note', ''),
        current_user=g.user,
    )
    if 'error' in res:
        return jsonify(res), res.get('status', 400)
    return jsonify(res)


@review_bp.post('/review/requests/acknowledge-resolved')
@role_required(['editor', 'reviewer'])
def acknowledge_resolved_requests_ep():
    res = clip_service.acknowledge_resolved_requests(current_user=g.user)
    if 'error' in res:
        return jsonify(res), res.get('status', 400)
    return jsonify(res)


@review_bp.post('/review/requests/assign')
@role_required(['admin'])
def assign_review_requests_ep():
    from services.auth_service import get_user_by_id

    data = request.get_json(force=True) or {}
    assignee = get_user_by_id(data.get('assignee_id'))
    if not assignee:
        return jsonify({'error': 'Assignee not found'}), 404

    res = clip_service.assign_review_requests(
        data.get('scene_keys', []),
        assignee,
        data.get('note', ''),
        current_user=g.user,
    )
    if 'error' in res:
        return jsonify(res), res.get('status', 400)
    return jsonify(res)
