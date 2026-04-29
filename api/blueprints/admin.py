"""Admin blueprint: /admin/overview, /admin/users, /admin/jobs"""
from flask import Blueprint, request, jsonify, g
from services import auth_service, clip_service
from api.decorators import role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.get('/overview')
@role_required(['admin'])
def admin_overview():
    from services.task_service import tasks_col
    from database.organized_videos_schema import _get_col
    from services.organized_video_service import get_label_counts
    user_counts = auth_service.get_user_summary_counts()
    ov_col = _get_col()
    total_organized = ov_col.count_documents({"status": "organized"})
    total_duplicates = ov_col.count_documents({"status": "duplicate"})
    label_counts = get_label_counts()
    recent_cursor = ov_col.find({"status": "organized"}).sort("created_at", -1).limit(5)
    recent_organized = []
    for doc in recent_cursor:
        recent_organized.append({
            "id": str(doc["_id"]),
            "display_name": doc.get("display_name"),
            "dominant_label": doc.get("dominant_label"),
            "created_at": doc.get("created_at"),
            "uploaded_by": doc.get("uploaded_by"),
        })

    # Recent failed tasks for the activity feed
    failed_cursor = tasks_col.find(
        {"status": "FAILURE"},
        {"task_id": 1, "type": 1, "input_path": 1, "created_at": 1, "updated_at": 1}
    ).sort("updated_at", -1).limit(3)
    recent_failures = []
    for t in failed_cursor:
        t["_id"] = str(t["_id"])
        recent_failures.append(t)

    return jsonify({
        'total_users': user_counts['total_users'],
        'active_users': user_counts['active_users'],
        'total_videos': len(clip_service.col.distinct('video')),
        'total_clips': clip_service.col.count_documents({}),
        'pending_review': clip_service.col.count_documents({'reviewed': False}),
        'uncertain_clips': clip_service.col.count_documents({'uncertain': True}),
        'tasks_running': tasks_col.count_documents({'status': {'$in': ['PENDING', 'STARTED']}}),
        'tasks_failed': tasks_col.count_documents({'status': 'FAILURE'}),
        'total_organized_videos': total_organized,
        'duplicate_videos': total_duplicates,
        'organized_by_label': label_counts,
        'recent_organized_uploads': recent_organized,
        'recent_failures': recent_failures,
    })


@admin_bp.get('/users')
@role_required(['admin'])
def get_users():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    search = request.args.get('search', '').strip()
    role = request.args.get('role', '').strip()
    status = request.args.get('status', '').strip()
    sort = request.args.get('sort', 'created_at').strip()
    order = request.args.get('order', 'desc').strip()
    return jsonify(auth_service.get_paginated_users(page, limit, search, role, status, sort, order))


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


@admin_bp.post('/jobs/<task_id>/retry')
@role_required(['admin'])
def retry_job_ep(task_id):
    """Re-dispatch a failed job of any type."""
    from services.task_service import get_job_by_task_id, tasks_col, insert_task_record
    from services.task_service import dispatch_process, dispatch_auto_organize

    job = get_job_by_task_id(task_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    if job.get('status') not in ('FAILURE', 'REVOKED'):
        return jsonify({'error': 'Only failed or revoked jobs can be retried'}), 400

    input_path = job.get('input_path')
    initiated_by = job.get('initiated_by')
    job_type = job.get('type', 'upload')

    if job_type == 'auto_organize':
        new_task = dispatch_auto_organize(input_path, initiated_by)
    else:
        new_task = dispatch_process(input_path, initiated_by)

    return jsonify({'ok': True, 'new_task_id': new_task.id})


@admin_bp.delete('/jobs/<task_id>')
@role_required(['admin'])
def cancel_job_ep(task_id):
    """Cancel a pending or running job."""
    from services.task_service import get_job_by_task_id, update_task_record
    from api.celery_worker import celery_app

    job = get_job_by_task_id(task_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    if job.get('status') not in ('PENDING', 'STARTED'):
        return jsonify({'error': 'Only pending or running jobs can be cancelled'}), 400

    celery_app.control.revoke(task_id, terminate=True, signal='SIGTERM')
    update_task_record(task_id, status='REVOKED', progress_step='Cancelled by admin')
    return jsonify({'ok': True, 'revoked': task_id})


@admin_bp.get('/assignments')
@role_required(['admin'])
def get_assignments():
    from services.clip_service import col
    # Return distinct videos with their assigned editor (if any), and progress (clips reviewed / total clips)
    pipeline = [
        {"$group": {
            "_id": "$video",
            "total_clips": {"$sum": 1},
            "reviewed_clips": {"$sum": {"$cond": [{"$eq": ["$reviewed", True]}, 1, 0]}},
            "assigned_to": {"$first": "$assigned_to"}
        }},
        {"$sort": {"_id": 1}}
    ]
    videos = list(col.aggregate(pipeline))
    return jsonify([
        {
            "video": v["_id"],
            "total_clips": v["total_clips"],
            "reviewed_clips": v["reviewed_clips"],
            "assigned_to": v.get("assigned_to")
        } for v in videos
    ])


@admin_bp.post('/assignments/assign')
@role_required(['admin'])
def assign_video():
    data = request.get_json(force=True) or {}
    video = data.get('video')
    user_id = data.get('user_id') # Can be None to unassign
    if not video:
        return jsonify({'error': 'video is required'}), 400
    
    # Verify user_id is valid editor/reviewer
    if user_id:
        from services.auth_service import get_user_by_id
        user = get_user_by_id(user_id)
        if not user or user.get('role') not in ('editor', 'reviewer', 'admin'):
            return jsonify({'error': 'Invalid user ID'}), 400
            
    from services.clip_service import col
    res = col.update_many(
        {"video": video},
        {"$set": {"assigned_to": user_id}}
    )
    return jsonify({'ok': True, 'modified_count': res.modified_count})

