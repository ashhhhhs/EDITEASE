"""Auth blueprint: /register, /login, /logout, /me, /forgot-password, /reset-password"""
import os
import secrets
import hashlib
import datetime

from flask import Blueprint, request, jsonify, g
from services import auth_service
from api.decorators import login_required, role_required

auth_bp = Blueprint('auth', __name__)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

@auth_bp.post('/register')
def register():
    data = request.get_json(force=True) or {}
    res = auth_service.register_user(
        email=data.get('email'),
        password=data.get('password'),
        name=data.get('name'),
    )
    if 'error' in res:
        return jsonify(res), res.get('status', 400)
    return jsonify(res)


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@auth_bp.post('/login')
def login():
    data = request.get_json(force=True) or {}
    res = auth_service.login_user(
        email=data.get('email'),
        password=data.get('password'),
    )
    if 'error' in res:
        return jsonify(res), res.get('status', 401)
    return jsonify(res)


# ---------------------------------------------------------------------------
# Logout / Session
# ---------------------------------------------------------------------------

@auth_bp.post('/logout')
@login_required
def logout():
    token = request.headers.get('Authorization', '').split(' ')[-1]
    return jsonify(auth_service.logout_user(token))


@auth_bp.get('/me')
@login_required
def get_me():
    return jsonify({'user': g.user})


# ---------------------------------------------------------------------------
# Forgot password
# ---------------------------------------------------------------------------

@auth_bp.post('/forgot-password')
def forgot_password():
    """Always returns 200 OK regardless of whether the email exists.

    This prevents account enumeration — an attacker cannot determine
    whether a given email is registered by observing the response.
    """
    from services.reset_token_service import create_and_send_reset_token

    data = request.get_json(force=True) or {}
    email = (data.get('email') or '').strip().lower()

    if email:
        # Fire and forget — errors are logged inside; user always sees success
        try:
            create_and_send_reset_token(email)
        except Exception:
            pass  # never surface internal errors to the client

    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Reset password
# ---------------------------------------------------------------------------

@auth_bp.post('/reset-password')
def reset_password():
    """Validate a reset token and update the user's password.

    On success:  200 {ok: true}
    On failure:  400 with a safe, non-revealing error message
    """
    from services.reset_token_service import validate_and_consume_token

    data = request.get_json(force=True) or {}
    raw_token = (data.get('token') or '').strip()
    new_password = data.get('password') or ''

    if not raw_token or not new_password:
        return jsonify({"error": "Token and new password are required."}), 400

    result = validate_and_consume_token(raw_token)
    if 'error' in result:
        return jsonify(result), 400

    user_id = result['user_id']
    res = auth_service.reset_password(user_id, new_password)
    if 'error' in res:
        return jsonify(res), res.get('status', 400)

    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Email Verification
# ---------------------------------------------------------------------------

@auth_bp.get('/verify-email/<token>')
def verify_email(token):
    from services.verification_service import verify_token
    res = verify_token(token)
    if 'error' in res:
        return jsonify(res), res.get('status', 400)
    return jsonify({"ok": True})


@auth_bp.post('/verify-email/resend')
@login_required
def resend_verification_email():
    from services.verification_service import resend_verification
    user = g.user
    if user.get('email_verified'):
        return jsonify({"error": "Email is already verified.", "status": 400}), 400
        
    res = resend_verification(user['id'], user['email'])
    if 'error' in res:
        return jsonify(res), res.get('status', 400)
    return jsonify({"ok": True})

# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------

@auth_bp.post('/auth/google')
def google_auth():
    """Verify Google token and login/register the user."""
    data = request.get_json(force=True) or {}
    token_str = data.get('token')
    if not token_str:
        return jsonify({"error": "Google token is required."}), 400

    res = auth_service.login_with_google(token_str)
    if 'error' in res:
        return jsonify(res), res.get('status', 400)

    return jsonify({
        "ok": True,
        "token": res['token'],
        "user": res['user']
    })


@auth_bp.post('/auth/google/link')
@login_required
def google_auth_link():
    """Link a Google account to an existing logged-in user."""
    data = request.get_json(force=True) or {}
    token_str = data.get('token')
    if not token_str:
        return jsonify({"error": "Google token is required."}), 400

    user_id = g.user.get("id")
    res = auth_service.link_google_account(user_id, token_str)
    if 'error' in res:
        return jsonify(res), res.get('status', 400)

    return jsonify({"ok": True})

# ---------------------------------------------------------------------------
# Team Invitations
# ---------------------------------------------------------------------------

@auth_bp.post('/invite')
@login_required
@role_required(['admin'])
def create_invite():
    from services.invitation_service import create_and_send_invitation
    data = request.get_json(force=True) or {}
    email = data.get('email')
    role = data.get('role', 'editor')
    
    if not email:
        return jsonify({"error": "Email is required.", "status": 400}), 400
        
    res = create_and_send_invitation(email, role, g.user['id'])
    if 'error' in res:
        return jsonify(res), res.get('status', 400)
    return jsonify({"ok": True})


@auth_bp.get('/invite/<token>')
def get_invite_info(token):
    from services.invitation_service import validate_invitation
    res = validate_invitation(token)
    if 'error' in res:
        return jsonify(res), res.get('status', 400)
    return jsonify(res)


@auth_bp.post('/invite/<token>/accept')
@login_required
def accept_invite_endpoint(token):
    from services.invitation_service import accept_invitation
    res = accept_invitation(token, g.user['id'], g.user['email'])
    if 'error' in res:
        return jsonify(res), res.get('status', 400)
    return jsonify(res)


# ---------------------------------------------------------------------------
# Account Settings
# ---------------------------------------------------------------------------

@auth_bp.patch('/user/password')
@login_required
def update_password():
    data = request.get_json(force=True) or {}
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({"error": "Current and new password are required."}), 400
        
    res = auth_service.update_user_password(g.user['id'], current_password, new_password)
    if 'error' in res:
        return jsonify(res), res.get('status', 400)
    return jsonify({"ok": True, "token": res["token"]})


@auth_bp.patch('/user/email')
@login_required
def update_email():
    data = request.get_json(force=True) or {}
    new_email = data.get('email')
    
    if not new_email:
        return jsonify({"error": "New email is required."}), 400
        
    res = auth_service.update_user_email(g.user['id'], new_email)
    if 'error' in res:
        return jsonify(res), res.get('status', 400)
    return jsonify({"ok": True})


@auth_bp.post('/user/logout-all')
@login_required
def logout_all():
    res = auth_service.sign_out_all_devices(g.user['id'])
    if 'error' in res:
        return jsonify(res), res.get('status', 400)
    return jsonify({"ok": True, "token": res["token"]})
