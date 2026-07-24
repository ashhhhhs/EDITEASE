"""
Shared pytest fixtures for the EditEase test suite.

Key responsibility: provide an in-memory MongoDB backend (mongomock) so tests
can run without a real MongoDB server.

- All MongoClient() calls within a test are intercepted by mongomock.patch,
  which routes them to an isolated in-memory database.
- Lazy-init _client singletons (auth_service, verification_service,
  invitation_service) are reset to None before each test so they reconnect
  through the mock on first use.
- Module-level collection references in clip_service (created at import time
  before any fixture runs) are replaced with a fresh mongomock collection for
  each test.
"""

import pytest
import mongomock


@pytest.fixture(autouse=True)
def mongo_patch(monkeypatch):
    fake_client = mongomock.MongoClient()
    monkeypatch.setattr("pymongo.MongoClient", lambda *_args, **_kwargs: fake_client)

    from services import auth_service, verification_service, invitation_service
    from services import clip_service, email_service, reset_token_service
    from database import organized_videos_schema

    monkeypatch.setattr(auth_service, "MongoClient", lambda *_args, **_kwargs: fake_client)
    monkeypatch.setattr(verification_service, "MongoClient", lambda *_args, **_kwargs: fake_client)
    monkeypatch.setattr(invitation_service, "MongoClient", lambda *_args, **_kwargs: fake_client)
    monkeypatch.setattr(email_service, "send_verification_email", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(email_service, "send_password_reset_email", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(email_service, "send_invitation_email", lambda *_args, **_kwargs: True)

    auth_service._client = None
    verification_service._client = None
    invitation_service._client = None
    reset_token_service._client = None
    organized_videos_schema._client = None

    fake_col = fake_client["editease"]["scenes"]
    monkeypatch.setattr(clip_service, "col", fake_col)

    yield

    auth_service._client = None
    verification_service._client = None
    invitation_service._client = None
    reset_token_service._client = None
    organized_videos_schema._client = None
