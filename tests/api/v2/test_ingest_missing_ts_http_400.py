from fastapi.testclient import TestClient
from api.main import app


def test_ingest_missing_ts_returns_400():
    client = TestClient(app)
    # create session
    resp = client.post("/api/v2/sessions")
    assert resp.status_code == 201
    sid = resp.json()["session_id"]

    # Post event without ts (conftest should not inject for this test path), expect 400
    # To ensure we test the mapping, post directly without ts by sending raw dict
    req = {"type": "QUOTE_INGESTED", "payload": {"v": 1}}
    r = client.post(f"/api/v2/sessions/{sid}/events", json=req, headers={"X-TS-INJECT": "false"})
    assert r.status_code == 400
    body = r.json()
    assert "category" in body["detail"]
    assert body["detail"]["category"] == "VALIDATION"
