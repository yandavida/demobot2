from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_compute_requested_happy_path():
    sid = client.post("/api/v2/sessions").json()["session_id"]
    req = {"type": "COMPUTE_REQUESTED", "payload": {"kind": "SNAPSHOT", "params": {"force": True}}}
    resp = client.post(f"/api/v2/sessions/{sid}/events", json=req)
    assert resp.status_code == 201
    body = resp.json()
    assert "state_version" in body
    assert "applied" in body

def test_compute_invalid_kind_is_400():
    sid = client.post("/api/v2/sessions").json()["session_id"]
    req = {"type": "COMPUTE_REQUESTED", "payload": {"kind": "NOPE", "params": {"x": 1}}}
    resp = client.post(f"/api/v2/sessions/{sid}/events", json=req)
    assert resp.status_code == 400

def test_compute_empty_params_is_400():
    sid = client.post("/api/v2/sessions").json()["session_id"]
    req = {"type": "COMPUTE_REQUESTED", "payload": {"kind": "SNAPSHOT", "params": {}}}
    resp = client.post(f"/api/v2/sessions/{sid}/events", json=req)
    assert resp.status_code == 400
