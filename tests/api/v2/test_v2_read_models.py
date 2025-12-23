from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def create_session():
    resp = client.post("/api/v2/sessions")
    assert resp.status_code == 201
    return resp.json()["session_id"]

def ingest_quote(session_id, payload):
    req = {"type": "QUOTE_INGESTED", "payload": payload}
    resp = client.post(f"/api/v2/sessions/{session_id}/events", json=req)
    assert resp.status_code == 201
    return resp.json()

def ingest_compute(session_id, kind, params):
    req = {"type": "COMPUTE_REQUESTED", "payload": {"kind": kind, "params": params}}
    resp = client.post(f"/api/v2/sessions/{session_id}/events", json=req)
    assert resp.status_code == 201
    return resp.json()

def test_list_events_default_excludes_payload():
    sid = create_session()
    ingest_quote(sid, {"foo": 1, "bar": 2})
    resp = client.get(f"/api/v2/sessions/{sid}/events")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == sid
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["payload"] is None
    assert item["payload_hash"]

def test_list_events_include_payload_true_returns_payload():
    sid = create_session()
    ingest_quote(sid, {"foo": 42})
    resp = client.get(f"/api/v2/sessions/{sid}/events?include_payload=true")
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    assert item["payload"] == {"foo": 42}

def test_snapshot_metadata_404_if_missing():
    sid = create_session()
    resp = client.get(f"/api/v2/sessions/{sid}/snapshot/metadata")
    assert resp.status_code == 404

def test_snapshot_metadata_returns_metadata_after_snapshot():
    sid = create_session()
    ingest_quote(sid, {"foo": 1})
    snap_resp = client.post(f"/api/v2/sessions/{sid}/snapshot")
    assert snap_resp.status_code in (200, 201)
    resp = client.get(f"/api/v2/sessions/{sid}/snapshot/metadata")
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == sid
    assert "state_version" in body
    assert "state_hash" in body
    assert "created_at" in body

def test_list_compute_requests_default_excludes_params():
    sid = create_session()
    ingest_compute(sid, "SNAPSHOT", {"force": True})
    resp = client.get(f"/api/v2/sessions/{sid}/compute/requests")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["params"] is None
    assert items[0]["params_hash"]

def test_unknown_session_returns_404():
    for url in [
        "/api/v2/sessions/doesnotexist/events",
        "/api/v2/sessions/doesnotexist/snapshot/metadata",
        "/api/v2/sessions/doesnotexist/compute/requests",
    ]:
        resp = client.get(url)
        assert resp.status_code == 404
