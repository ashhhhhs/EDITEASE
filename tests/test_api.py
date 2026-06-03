import pytest
import os
import json

from api.api_server import app
from database import ingest_to_mongo
from services import cloudinary_service

_TEST_USER = {
    "id": "000000000000000000000001",
    "email": "admin@test.com",
    "name": "Test Admin",
    "role": "admin",
    "email_verified": True,
    "is_active": True,
    "created_at": None,
    "last_login_at": None,
}

@pytest.fixture
def client(monkeypatch):
    from services import auth_service
    monkeypatch.setattr(auth_service, "get_user_by_token", lambda t: _TEST_USER)
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c

def test_health_endpoint(client):
    """Test that the health endpoint returns 200 OK and expected structure."""
    rv = client.get('/health')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert 'ok' in data
    assert data['ok'] is True

def test_search_endpoint_basic(client):
    """Test that search endpoint returns a 200 OK with valid parameters."""
    rv = client.get('/search?limit=5')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert 'results' in data
    assert isinstance(data['results'], list)

def test_upload_endpoint_no_file(client):
    """Test that the upload endpoint correctly rejects requests without a file."""
    rv = client.post('/upload')
    assert rv.status_code == 400
    data = json.loads(rv.data)
    assert 'error' in data
    
def test_update_scene_missing_params(client):
    """Test that update_scene requires video and scene_id."""
    rv = client.post('/update_scene', json={"scene_label": "b-roll"})
    assert rv.status_code == 400
    data = json.loads(rv.data)
    assert data['error'] == "video and scene_id required"

def test_export_missing_params(client):
    """Test that /export rejects requests without video and scene_id."""
    rv = client.post('/export', json={})
    assert rv.status_code == 400
    data = json.loads(rv.data)
    assert 'error' in data

def test_export_batch_empty(client):
    """Test that /export_batch with no matching data returns zero counts."""
    rv = client.post('/export_batch', json={"video": "nonexistent_video_xyz"})
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data.get('exported_count', 0) == 0

def test_auto_organize_no_file(client):
    """Test that /auto_organize rejects requests without a file."""
    rv = client.post('/auto_organize')
    assert rv.status_code == 400
    data = json.loads(rv.data)
    assert 'error' in data


def test_delete_selected_organized_videos(client, monkeypatch):
    """Organized-video deletion removes selected records and unreferenced cloud assets."""
    import mongomock
    from bson import ObjectId
    from services import organized_video_service, cloudinary_service

    fake_col = mongomock.MongoClient()["editease"]["organized_videos"]
    delete_id = ObjectId()
    keep_id = ObjectId()
    fake_col.insert_many([
        {
            "_id": delete_id,
            "display_name": "Delete Me",
            "original_filename": "delete.mp4",
            "dominant_label": "presenter",
            "status": "organized",
            "uploaded_by": _TEST_USER["id"],
            "cloudinary_public_id": "editease/organized-videos/presenter/delete",
            "cloudinary_url": "https://example.test/delete.mp4",
            "created_at": "2026-05-22T00:00:00",
        },
        {
            "_id": keep_id,
            "display_name": "Keep Me",
            "original_filename": "keep.mp4",
            "dominant_label": "presenter",
            "status": "organized",
            "uploaded_by": _TEST_USER["id"],
            "cloudinary_public_id": "editease/organized-videos/presenter/keep",
            "cloudinary_url": "https://example.test/keep.mp4",
            "created_at": "2026-05-22T00:00:00",
        },
    ])
    monkeypatch.setattr(organized_video_service, "_get_col", lambda: fake_col)

    deleted_assets = []
    monkeypatch.setattr(
        cloudinary_service,
        "delete_asset",
        lambda public_id, resource_type="image": deleted_assets.append((public_id, resource_type)) or True,
    )

    rv = client.delete('/organized-videos', json={"ids": [str(delete_id)]})

    assert rv.status_code == 200
    data = rv.get_json()
    assert data["deleted_count"] == 1
    assert fake_col.find_one({"_id": delete_id}) is None
    assert fake_col.find_one({"_id": keep_id}) is not None
    assert deleted_assets == [("editease/organized-videos/presenter/delete", "video")]


def test_organized_video_search_treats_parentheses_literally(client, monkeypatch):
    """Filename search should not fail when video names contain regex characters."""
    import mongomock
    from services import organized_video_service

    fake_col = mongomock.MongoClient()["editease"]["organized_videos"]
    fake_col.insert_one({
        "display_name": "C3864(1)",
        "original_filename": "C3864(1).mp4",
        "dominant_label": "b-roll",
        "status": "organized",
        "uploaded_by": _TEST_USER["id"],
        "cloudinary_public_id": "editease/organized-videos/b-roll/c3864-1",
        "cloudinary_url": "https://example.test/C3864(1).mp4",
        "created_at": "2026-05-22T00:00:00",
    })
    monkeypatch.setattr(organized_video_service, "_get_col", lambda: fake_col)

    rv = client.get(
        '/organized-videos?label=b-roll&search=C3864(1)',
        headers={"Origin": "http://localhost:5173"},
    )

    assert rv.status_code == 200
    assert rv.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    data = rv.get_json()
    assert data["total"] == 1
    assert data["videos"][0]["original_filename"] == "C3864(1).mp4"


def test_editor_sees_review_related_organized_videos(client, monkeypatch):
    """Editors should see organized videos connected to clips they reviewed."""
    import mongomock
    from services import auth_service, clip_service, organized_video_service

    editor = {
        **_TEST_USER,
        "id": "editor-2",
        "email": "editor2@test.com",
        "role": "editor",
    }
    monkeypatch.setattr(auth_service, "get_user_by_token", lambda t: editor)

    fake_clip_col = mongomock.MongoClient()["editease"]["scenes"]
    monkeypatch.setattr(clip_service, "col", fake_clip_col)
    fake_clip_col.insert_one({
        "_key": "client-video::1",
        "video": "client-video",
        "scene_id": 1,
        "uploaded_by": "owner-1",
        "assigned_to": "editor-2",
        "review_resolved_by": "editor-2",
        "review_request_status": "resolved",
        "reviewed": True,
    })

    organized_col = mongomock.MongoClient()["editease"]["organized_videos"]
    organized_col.insert_one({
        "display_name": "Client Video",
        "original_filename": "client-video.mp4",
        "safe_name": "client-video",
        "dominant_label": "b-roll",
        "status": "organized",
        "uploaded_by": "owner-1",
        "cloudinary_public_id": "editease/organized-videos/b-roll/client-video",
        "cloudinary_url": "https://example.test/client-video.mp4",
        "created_at": "2026-05-22T00:00:00",
    })
    monkeypatch.setattr(organized_video_service, "_get_col", lambda: organized_col)

    list_rv = client.get('/organized-videos?label=b-roll&search=client-video')
    stats_rv = client.get('/organized-videos/stats')

    assert list_rv.status_code == 200
    assert list_rv.get_json()["total"] == 1
    assert list_rv.get_json()["videos"][0]["original_filename"] == "client-video.mp4"
    assert list_rv.get_json()["videos"][0]["can_delete"] is False
    assert stats_rv.status_code == 200
    assert stats_rv.get_json()["b-roll"] == 1

    delete_rv = client.delete('/organized-videos', json={"ids": [list_rv.get_json()["videos"][0]["id"]]})
    assert delete_rv.status_code == 403
    assert "Only the uploader" in delete_rv.get_json()["error"]


def test_reviewer_role_is_assignable(client, monkeypatch):
    """Reviewer is an active role in the admin role endpoint."""
    from services import auth_service

    monkeypatch.setattr(
        auth_service,
        "update_user_role",
        lambda target_id, new_role, requester_id: {"ok": True, "new_role": new_role},
    )

    rv = client.patch(
        '/admin/users/507f1f77bcf86cd799439011/role',
        json={"role": "reviewer"},
    )
    assert rv.status_code == 200
    assert rv.get_json()["new_role"] == "reviewer"


def test_job_list_includes_initiating_user(monkeypatch):
    """Admin job payloads should identify who triggered each task."""
    import mongomock
    from bson import ObjectId
    from services import task_service

    fake_db = mongomock.MongoClient()["editease"]
    fake_tasks = fake_db["tasks"]
    fake_users = fake_db["users"]
    user_id = ObjectId()

    fake_users.insert_one({
        "_id": user_id,
        "name": "Clip Reviewer",
        "email": "reviewer@example.com",
        "role": "reviewer",
    })
    fake_tasks.insert_one({
        "task_id": "task-123",
        "type": "upload",
        "status": "SUCCESS",
        "created_at": "2026-05-25T10:00:00",
        "updated_at": "2026-05-25T10:01:00",
        "started_at": "2026-05-25T10:00:00",
        "completed_at": "2026-05-25T10:01:00",
        "initiated_by": str(user_id),
        "input_path": "demo.mp4",
    })
    monkeypatch.setattr(task_service, "tasks_col", fake_tasks)

    data = task_service.get_paginated_jobs()

    assert data["jobs"][0]["initiated_by_user"] == {
        "id": str(user_id),
        "name": "Clip Reviewer",
        "email": "reviewer@example.com",
        "role": "reviewer",
    }


def test_task_status_falls_back_to_mongo_when_celery_is_unavailable(monkeypatch):
    """Completed task polling should survive a temporary Celery/Redis status failure."""
    import mongomock
    from services import task_service

    fake_db = mongomock.MongoClient()["editease"]
    fake_tasks = fake_db["tasks"]
    fake_tasks.insert_one({
        "task_id": "task-auto-1",
        "type": "auto_organize",
        "status": "SUCCESS",
        "progress_step": "done",
        "output_path": "editease/organized-videos/b-roll/hash/demo",
    })
    fake_db["organized_videos"].insert_one({
        "batch_id": "task-auto-1",
        "original_filename": "demo.mp4",
        "status": "organized",
        "dominant_label": "b-roll",
        "cloudinary_public_id": "editease/organized-videos/b-roll/hash/demo",
        "ai_metadata": {"total_scenes_detected": 2},
        "created_at": "2026-05-28T10:00:00",
    })

    class BrokenCelery:
        def AsyncResult(self, _task_id):
            raise RuntimeError("redis unavailable")

    monkeypatch.setattr(task_service, "db", fake_db)
    monkeypatch.setattr(task_service, "tasks_col", fake_tasks)
    monkeypatch.setattr(task_service, "celery_app", BrokenCelery())

    data = task_service.get_task_status("task-auto-1")

    assert data["status"] == "SUCCESS"
    assert data["result"]["video"] == "demo"
    assert data["result"]["dominant_label"] == "b-roll"
    assert data["result"]["ai_metadata"]["total_scenes_detected"] == 2


def test_cloudinary_service_upload_mock(monkeypatch):
    """Cloudinary upload helper should return the secure CDN URL from the SDK."""
    monkeypatch.setattr(cloudinary_service, "is_configured", lambda: True)

    calls = []

    def fake_upload(local_path, **opts):
        calls.append((local_path, opts))
        return {"secure_url": "https://res.cloudinary.com/demo/video/upload/sample.mp4"}

    monkeypatch.setattr(cloudinary_service.cloudinary.uploader, "upload_large", fake_upload)

    result = cloudinary_service.upload_video(
        "D:/EDITEASE/data/sample.mp4",
        public_id="editease/videos/sample",
    )

    assert result == "https://res.cloudinary.com/demo/video/upload/sample.mp4"
    assert calls == [(
        "D:/EDITEASE/data/sample.mp4",
        {"resource_type": "video", "public_id": "editease/videos/sample"},
    )]


def test_upsert_scene_docs_builds_keys_and_persists(monkeypatch):
    """Scene ingestion should create Mongo-ready keys and preserve Cloudinary fields."""

    class FakeCollection:
        def __init__(self):
            self.index_calls = []
            self.update_calls = []

        def create_index(self, spec, unique=False):
            self.index_calls.append((spec, unique))

        def update_one(self, query, update, upsert=False):
            self.update_calls.append((query, update, upsert))

    class FakeDatabase:
        def __init__(self, collection):
            self.collection = collection

        def __getitem__(self, name):
            return self.collection

    class FakeClient:
        def __init__(self, collection):
            self.collection = collection

        def __getitem__(self, name):
            return FakeDatabase(self.collection)

    fake_collection = FakeCollection()
    monkeypatch.setattr(ingest_to_mongo, "MongoClient", lambda uri: FakeClient(fake_collection))

    upserted = ingest_to_mongo.upsert_scene_docs([
        {
            "video": "demo",
            "scene_id": 3,
            "cloudinary_url": "https://res.cloudinary.com/demo/video/upload/demo.mp4",
            "thumbnail_url": "https://res.cloudinary.com/demo/image/upload/demo.jpg",
        }
    ], source_name="demo_scene_index.json")

    assert upserted == 1
    assert fake_collection.index_calls
    assert fake_collection.update_calls == [(
        {"_key": "demo::3"},
        {"$set": {
            "video": "demo",
            "scene_id": 3,
            "cloudinary_url": "https://res.cloudinary.com/demo/video/upload/demo.mp4",
            "thumbnail_url": "https://res.cloudinary.com/demo/image/upload/demo.jpg",
            "_key": "demo::3",
        }},
        True,
    )]
