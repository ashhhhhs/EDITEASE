import pytest
import os
import json
import datetime
from bson import ObjectId

from api.api_server import app as _app
from services import auth_service, reset_token_service
import config

@pytest.fixture
def app():
    # Use a test database name
    original_db = config.DB_NAME
    config.DB_NAME = "editease_test_db"
    
    _app.config['TESTING'] = True
    
    # Clear test db collections
    from pymongo import MongoClient
    client = MongoClient(config.MONGO_URI)
    db = client[config.DB_NAME]
    db.users.delete_many({})
    db.password_reset_tokens.delete_many({})
    db.email_verification_tokens.delete_many({})
    try:
        db.users.drop_index("username_1")
    except Exception:
        pass
    
    yield _app
    
    # Cleanup
    db.users.delete_many({})
    db.password_reset_tokens.delete_many({})
    db.email_verification_tokens.delete_many({})
    config.DB_NAME = original_db

@pytest.fixture
def client(app):
    return app.test_client()

def test_register_and_login(client):
    # 1. Register
    rv = client.post('/register', json={
        "email": "test@example.com",
        "password": "StrongPassword123!",
        "name": "Test User"
    })
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["ok"] is True
    
    # Verify default role is editor
    from pymongo import MongoClient
    db = MongoClient(config.MONGO_URI)[config.DB_NAME]
    user = db.users.find_one({"email": "test@example.com"})
    assert user["role"] == "editor"
    
    # 2. Login
    rv = client.post('/login', json={
        "email": "test@example.com",
        "password": "StrongPassword123!"
    })
    assert rv.status_code == 200
    data = rv.get_json()
    assert "token" in data
    assert data["user"]["email"] == "test@example.com"
    
    # 3. Get /me
    rv = client.get('/me', headers={"Authorization": f"Bearer {data['token']}"})
    assert rv.status_code == 200
    me_data = rv.get_json()
    assert me_data["user"]["email"] == "test@example.com"

def test_register_rejects_mismatched_confirm_password(client):
    rv = client.post('/register', json={
        "email": "mismatch@example.com",
        "password": "StrongPassword123!",
        "confirm_password": "WrongPassword123!",
        "name": "Mismatch User"
    })
    assert rv.status_code == 400
    assert rv.get_json()["error"] == "Passwords do not match."

def test_login_failures(client):
    # Register first
    client.post('/register', json={
        "email": "test2@example.com",
        "password": "StrongPassword123!"
    })
    
    # Wrong password
    rv = client.post('/login', json={
        "email": "test2@example.com",
        "password": "WrongPassword!"
    })
    assert rv.status_code == 401
    err_wrong = rv.get_json()["error"]
    
    # Non-existent email
    rv = client.post('/login', json={
        "email": "nobody@example.com",
        "password": "StrongPassword123!"
    })
    assert rv.status_code == 401
    err_none = rv.get_json()["error"]
    
    # Must be identical to prevent enumeration
    assert err_wrong == err_none

def test_forgot_password_no_enumeration(client):
    # Register
    client.post('/register', json={
        "email": "test3@example.com",
        "password": "StrongPassword123!"
    })
    
    # Request for real email
    rv = client.post('/forgot-password', json={"email": "test3@example.com"})
    assert rv.status_code == 200
    assert rv.get_json()["ok"] is True
    
    # Request for fake email
    rv = client.post('/forgot-password', json={"email": "notreal@example.com"})
    assert rv.status_code == 200
    assert rv.get_json()["ok"] is True
    
    # Verify token was only created for real email
    from pymongo import MongoClient
    db = MongoClient(config.MONGO_URI)[config.DB_NAME]
    assert db.password_reset_tokens.count_documents({}) == 1

def test_reset_password_flow(client, monkeypatch):
    # 1. Register User
    client.post('/register', json={
        "email": "resetit@example.com",
        "password": "OldPassword123!"
    })
    
    # 2. Login to get an active session
    rv = client.post('/login', json={
        "email": "resetit@example.com",
        "password": "OldPassword123!"
    })
    old_token = rv.get_json()["token"]
    
    # 3. Mock create_token to catch the raw token (since we aren't sending emails)
    raw_token = None
    original_create = reset_token_service.create_and_send_reset_token
    
    def mock_create(email):
        nonlocal raw_token
        import secrets
        raw_token = secrets.token_urlsafe(32)
        token_hash = reset_token_service._hash_token(raw_token)
        col = reset_token_service._get_col()
        user = reset_token_service._get_users_col().find_one({"email": email})
        now = datetime.datetime.utcnow()
        col.insert_one({
            "user_id": str(user["_id"]),
            "token_hash": token_hash,
            "created_at": now.isoformat(),
            "expires_at": now + datetime.timedelta(minutes=15),
            "used_at": None
        })
    
    monkeypatch.setattr(reset_token_service, "create_and_send_reset_token", mock_create)
    
    # 4. Trigger forgot password
    client.post('/forgot-password', json={"email": "resetit@example.com"})
    assert raw_token is not None
    
    # 5. Reset with wrong token
    rv = client.post('/reset-password', json={
        "token": "fake_token_value",
        "password": "NewPassword123!"
    })
    assert rv.status_code == 400
    
    # 6. Reset with valid token
    rv = client.post('/reset-password', json={
        "token": raw_token,
        "password": "NewPassword123!"
    })
    assert rv.status_code == 200
    
    # 7. Check if old session is invalidated
    rv = client.get('/me', headers={"Authorization": f"Bearer {old_token}"})
    assert rv.status_code == 401
    
    # 8. Login with new password
    rv = client.post('/login', json={
        "email": "resetit@example.com",
        "password": "NewPassword123!"
    })
    assert rv.status_code == 200
    
    # 9. Try to reuse token
    rv = client.post('/reset-password', json={
        "token": raw_token,
        "password": "AnotherPassword123!"
    })
    assert rv.status_code == 400
    assert "used" in rv.get_json()["error"]


# ---------------------------------------------------------------------------
# Phase 3 — Email Verification Tests
# ---------------------------------------------------------------------------

def _setup_verified_user(client):
    """Helper: register a user and mark them verified in DB."""
    rv = client.post('/register', json={
        "email": "verified@example.com",
        "password": "Password123!"
    })
    user_id = rv.get_json()["user_id"]
    from pymongo import MongoClient
    from bson import ObjectId
    db = MongoClient(config.MONGO_URI)[config.DB_NAME]
    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"email_verified": True}})
    rv = client.post('/login', json={"email": "verified@example.com", "password": "Password123!"})
    return rv.get_json()["token"]


def test_email_verification_token_flow(client, monkeypatch):
    """A valid verification token should mark the user verified."""
    from services import verification_service

    raw_token = None
    original_send = verification_service.send_verification_email

    def mock_send(email, rt):
        nonlocal raw_token
        raw_token = rt  # capture raw token (not sent via email in tests)

    monkeypatch.setattr(verification_service, "send_verification_email", mock_send)

    # Register (triggers create_and_send_verification)
    rv = client.post('/register', json={
        "email": "unverified@example.com",
        "password": "Password123!"
    })
    assert rv.status_code == 200
    assert raw_token is not None

    # User is unverified at login
    # Use valid token to verify
    rv = client.get(f'/verify-email/{raw_token}')
    assert rv.status_code == 200
    assert rv.get_json()["ok"] is True

    # User should now be verified
    from pymongo import MongoClient
    db = MongoClient(config.MONGO_URI)[config.DB_NAME]
    user = db.users.find_one({"email": "unverified@example.com"})
    assert user["email_verified"] is True


def test_email_verification_invalid_token(client):
    """An invalid/non-existent token returns 400."""
    rv = client.get('/verify-email/completelyfaketoken123')
    assert rv.status_code == 400
    assert "error" in rv.get_json()


def test_email_verification_expired_token(client, monkeypatch):
    """An expired token should return 400."""
    from services import verification_service
    from pymongo import MongoClient
    import hashlib, datetime

    raw_token = None

    def mock_send(email, rt):
        nonlocal raw_token
        raw_token = rt

    monkeypatch.setattr(verification_service, "send_verification_email", mock_send)

    rv = client.post('/register', json={
        "email": "expiry@example.com",
        "password": "Password123!"
    })
    assert raw_token is not None

    # Manually back-date the token in DB
    db = MongoClient(config.MONGO_URI)[config.DB_NAME]
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    past = (datetime.datetime.utcnow() - datetime.timedelta(hours=25)).isoformat()
    db.email_verification_tokens.update_one(
        {"token_hash": token_hash},
        {"$set": {"expires_at": past}}
    )

    rv = client.get(f'/verify-email/{raw_token}')
    assert rv.status_code == 400
    assert "error" in rv.get_json()


def test_email_verification_already_used_token(client, monkeypatch):
    """A token used twice should return 400 on second use."""
    from services import verification_service

    raw_token = None

    def mock_send(email, rt):
        nonlocal raw_token
        raw_token = rt

    monkeypatch.setattr(verification_service, "send_verification_email", mock_send)

    client.post('/register', json={"email": "alreadyused@example.com", "password": "Password123!"})
    assert raw_token is not None

    # Use it once — should succeed
    rv = client.get(f'/verify-email/{raw_token}')
    assert rv.status_code == 200

    # Use it again — should fail
    rv = client.get(f'/verify-email/{raw_token}')
    assert rv.status_code == 400


def test_login_throttled_after_repeated_failures(client, monkeypatch):
    """S6: repeated bad passwords must eventually return 429, not unlimited 401s."""
    from services import auth_service, verification_service
    monkeypatch.setattr(verification_service, "send_verification_email", lambda e, t: None)

    client.post('/register', json={"email": "throttle@example.com", "password": "Password123!"})

    codes = []
    for _ in range(auth_service.LOGIN_MAX_ATTEMPTS + 1):
        rv = client.post('/login', json={"email": "throttle@example.com", "password": "wrong"})
        codes.append(rv.status_code)

    assert codes[0] == 401, f"first bad attempt should be 401, got {codes[0]}"
    assert codes[-1] == 429, f"attempt past the limit should be 429, got {codes}"


def test_login_throttle_does_not_leak_account_existence(client):
    """S6: unknown emails must also be throttled, or the 429 becomes an oracle."""
    from services import auth_service

    for _ in range(auth_service.LOGIN_MAX_ATTEMPTS + 1):
        rv = client.post('/login', json={"email": "ghost@example.com", "password": "wrong"})

    assert rv.status_code == 429, (
        "an unknown email must throttle the same way a real one does, "
        "otherwise the response distinguishes real accounts"
    )


def test_successful_login_clears_throttle(client, monkeypatch):
    """S6: a correct password resets the failure counter."""
    from services import auth_service, verification_service
    monkeypatch.setattr(verification_service, "send_verification_email", lambda e, t: None)

    client.post('/register', json={"email": "clears@example.com", "password": "Password123!"})

    # Burn attempts, but stay one under the limit.
    for _ in range(auth_service.LOGIN_MAX_ATTEMPTS - 1):
        client.post('/login', json={"email": "clears@example.com", "password": "wrong"})

    rv = client.post('/login', json={"email": "clears@example.com", "password": "Password123!"})
    assert rv.status_code == 200

    # Counter cleared, so a fresh bad attempt is 401 rather than an immediate 429.
    rv = client.post('/login', json={"email": "clears@example.com", "password": "wrong"})
    assert rv.status_code == 401


def test_download_blocked_for_unverified_user(client, monkeypatch):
    """A require_verified_email route must 403 EMAIL_UNVERIFIED for an unverified user."""
    from services import verification_service
    monkeypatch.setattr(verification_service, "send_verification_email", lambda e, t: None)

    rv = client.post('/register', json={"email": "noexport@example.com", "password": "Password123!"})
    rv = client.post('/login', json={"email": "noexport@example.com", "password": "Password123!"})
    token = rv.get_json()["token"]

    rv = client.post('/organized-videos/download', json={"id": "abc123"},
                     headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code == 403
    data = rv.get_json()
    assert data.get("code") == "EMAIL_UNVERIFIED"


def test_download_allowed_for_verified_user(client, monkeypatch):
    """A verified user must clear the email gate (the route may still fail for other reasons)."""
    from services import verification_service
    monkeypatch.setattr(verification_service, "send_verification_email", lambda e, t: None)

    # Register and manually set verified
    rv = client.post('/register', json={"email": "doexport@example.com", "password": "Password123!"})
    user_id = rv.get_json()["user_id"]
    from pymongo import MongoClient
    from bson import ObjectId
    db = MongoClient(config.MONGO_URI)[config.DB_NAME]
    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"email_verified": True}})

    rv = client.post('/login', json={"email": "doexport@example.com", "password": "Password123!"})
    token = rv.get_json()["token"]

    # Should NOT get 403 EMAIL_UNVERIFIED (the route may still 404 for other reasons)
    rv = client.post('/organized-videos/download', json={"id": "nonexistent999"},
                     headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code != 403 or rv.get_json().get("code") != "EMAIL_UNVERIFIED"


def test_resend_verification_rate_limited(client, monkeypatch):
    """Resend after rate limit (3/hour) should return 429."""
    from services import verification_service
    send_calls = []
    monkeypatch.setattr(verification_service, "send_verification_email", lambda e, t: send_calls.append(t))

    client.post('/register', json={"email": "ratelimit@example.com", "password": "Password123!"})
    rv = client.post('/login', json={"email": "ratelimit@example.com", "password": "Password123!"})
    token = rv.get_json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Should succeed 2 more times (1 sent on register, 2 more = 3 total)
    client.post('/verify-email/resend', headers=headers)
    client.post('/verify-email/resend', headers=headers)

    # 4th should be rate-limited
    rv = client.post('/verify-email/resend', headers=headers)
    assert rv.status_code == 429
