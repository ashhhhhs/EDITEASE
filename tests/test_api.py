import pytest
import os
import json

from api.api_server import app
from database import ingest_to_mongo
from services import cloudinary_service

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

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


def test_cloudinary_service_upload_mock(monkeypatch):
    """Cloudinary upload helper should return the secure CDN URL from the SDK."""
    monkeypatch.setattr(cloudinary_service, "is_configured", lambda: True)

    calls = []

    def fake_upload(local_path, **opts):
        calls.append((local_path, opts))
        return {"secure_url": "https://res.cloudinary.com/demo/video/upload/sample.mp4"}

    monkeypatch.setattr(cloudinary_service.cloudinary.uploader, "upload", fake_upload)

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
