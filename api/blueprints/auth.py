"""Auth blueprint: /register, /login, /logout, /me"""
from flask import Blueprint, request, jsonify, g
from services import auth_service
from api.decorators import login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.post('/register')
def register():
    data = request.get_json(force=True) or {}
    res = auth_service.register_user(data.get('username'), data.get('password'), data.get('name'), data.get('email'))
    if 'error' in res:
        return jsonify(res), res.get('status', 400)
    return jsonify(res)

@auth_bp.post('/login')
def login():
    data = request.get_json(force=True) or {}
    res = auth_service.login_user(data.get('username'), data.get('password'))
    if 'error' in res:
        return jsonify(res), res.get('status', 401)
    return jsonify(res)

@auth_bp.post('/logout')
@login_required
def logout():
    token = request.headers.get('Authorization').split(' ')[1]
    return jsonify(auth_service.logout_user(token))

@auth_bp.get('/me')
@login_required
def get_me():
    return jsonify({'user': g.user})
