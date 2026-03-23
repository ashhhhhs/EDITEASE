"""Admin blueprint: /admin/overview, /admin/users, /admin/jobs"""
from flask import Blueprint, request, jsonify, g
from services import auth_service, clip_service
from api.decorators import role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.get('/overview')
@role_required(['admin'])
def admin_overview():
    from services.task_service import tasks_col
    user_counts = auth_service.get_user_summary_counts()
    return jsonify({
        'total_users': user_counts['total_users'],
        'active_users': user_counts['active_users'],
        'total_videos': len(clip_service.col.distinct('video')),
        'total_clips': clip_service.col.count_documents({}),
        'pending_review': clip_service.col.count_documents({'reviewed': False}),
        'uncertain_clips': clip_service.col.count_documents({'uncertain': True}),
        'tasks_running': tasks_col.count_documents({'status': {'$in': ['PENDING', 'STARTED']}}),
        'tasks_failed': tasks_col.count_documents({'status': 'FAILURE'}),
    })

@admin_bp.get('/users')
@role_required(['admin'])
def get_users():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    return jsonify(auth_service.get_paginated_users(page, limit))

@admin_bp.patch('/users/<target_id>/role')
@role_required(['admin'])
def update_user_role_ep(target_id):
    data = request.get_json(force=True) or {}
    new_role = data.get('role')
    if new_role not in ['admin', 'editor', 'reviewer']:
        return jsonify({'error': 'Invalid role'}), 400
    res = auth_service.update_user_role(target_id, new_role, str(g.user['id']))
    if 'error' in res:
        return jsonify(res), res.get('status', 400)
    return jsonify(res)

@admin_bp.patch('/users/<target_id>/status')
@role_required(['admin'])
def update_user_status_ep(target_id):
    data = request.get_json(force=True) or {}
    is_active = data.get('is_active')
    if is_active is None:
        return jsonify({'error': 'is_active boolean required'}), 400
    res = auth_service.update_user_status(target_id, bool(is_active), str(g.user['id']))
    if 'error' in res:
        return jsonify(res), res.get('status', 400)
    return jsonify(res)

@admin_bp.get('/jobs')
@role_required(['admin'])
def get_jobs():
    from services.task_service import get_paginated_jobs
    return jsonify(get_paginated_jobs(
        request.args.get('page', 1, type=int),
        request.args.get('limit', 20, type=int),
        request.args.get('status'),
        request.args.get('type'),
    ))

@admin_bp.get('/jobs/<task_id>')
@role_required(['admin'])
def get_job_detail_ep(task_id):
    from services.task_service import get_job_by_task_id
    job = get_job_by_task_id(task_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(job)
