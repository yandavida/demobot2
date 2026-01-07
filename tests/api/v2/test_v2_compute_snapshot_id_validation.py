from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_missing_market_snapshot_id_is_400():
    sid = client.post("/api/v2/sessions").json()["session_id"]
    # provide non-empty params so the validator reaches market_snapshot_id check
    req = {"type": "COMPUTE_REQUESTED", "payload": {"kind": "SNAPSHOT", "params": {"foo": 1}}}
    resp = client.post(f"/api/v2/sessions/{sid}/events", json=req)
    assert resp.status_code == 400
    body = resp.json()
    assert "detail" in body
    assert body["detail"]["code"] == "missing_market_snapshot_id"


def test_invalid_market_snapshot_id_is_400():
    sid = client.post("/api/v2/sessions").json()["session_id"]
    req = {"type": "COMPUTE_REQUESTED", "payload": {"kind": "SNAPSHOT", "params": {"market_snapshot_id": "not-a-hex"}}}
    resp = client.post(f"/api/v2/sessions/{sid}/events", json=req)
    assert resp.status_code == 400
    body = resp.json()
    assert "detail" in body
    assert body["detail"]["code"] == "invalid_market_snapshot_id"
