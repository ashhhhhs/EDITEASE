import pytest
import os
import json

from api.api_server import app

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
