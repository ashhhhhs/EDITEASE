"""Shared decorator utilities used by all blueprints."""
from functools import wraps
from flask import request, jsonify, g
from services import auth_service

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '')
        if token.startswith('Bearer '):
            token = token.split(' ', 1)[1]
        user = auth_service.get_user_by_token(token)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        g.user = user
        return f(*args, **kwargs)
    return decorated

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization', '')
            if token.startswith('Bearer '):
                token = token.split(' ', 1)[1]
            user = auth_service.get_user_by_token(token)
            if not user:
                return jsonify({'error': 'Unauthorized'}), 401
            if user.get('role') not in allowed_roles:
                return jsonify({'error': 'Forbidden: insufficient role'}), 403
            g.user = user
            return f(*args, **kwargs)
        return decorated
    return decorator

def require_verified_email(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Assumes login_required has already populated g.user
        user = getattr(g, 'user', None)
        if not user or not user.get('email_verified'):
            return jsonify({'error': 'Email verification required', 'code': 'EMAIL_UNVERIFIED'}), 403
        return f(*args, **kwargs)
    return decorated
