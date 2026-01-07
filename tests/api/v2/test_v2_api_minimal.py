import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.v2.service import enable_force_raise_for_tests, reset_for_tests

client = TestClient(app, raise_server_exceptions=True)

@pytest.fixture(autouse=True)
def reset_service():
    reset_for_tests()


def test_500_correlation_id_provided():
    enable_force_raise_for_tests(True)
    resp = client.post("/api/v2/sessions", headers={"X-Correlation-Id": "cid-500"})
    assert resp.status_code == 500
    assert resp.headers["X-Correlation-Id"] == "cid-500"
    assert resp.json() == {
        "detail": {
            "category": "SERVER",
            "code": "internal_error",
            "message": "Internal Server Error",
            "details": {},
            "error_count": 1,
        }
    }

def test_500_correlation_id_autogen():
    enable_force_raise_for_tests(True)
    resp = client.post("/api/v2/sessions")
    assert resp.status_code == 500
    assert "X-Correlation-Id" in resp.headers
    assert resp.headers["X-Correlation-Id"]
    assert resp.json() == {
        "detail": {
            "category": "SERVER",
            "code": "internal_error",
            "message": "Internal Server Error",
            "details": {},
            "error_count": 1,
        }
    }


def test_correlation_id_passthrough():
    cid = "test-cid-1"
    resp = client.post("/api/v2/sessions", headers={"X-Correlation-Id": cid})
    assert resp.status_code == 201
    assert resp.headers["X-Correlation-Id"] == cid


def test_correlation_id_autogen():
    resp = client.post("/api/v2/sessions")
    assert resp.status_code == 201
    assert "X-Correlation-Id" in resp.headers
    assert resp.headers["X-Correlation-Id"]


def test_idempotent_ingest():
    # Create session
    resp = client.post("/api/v2/sessions")
    session_id = resp.json()["session_id"]
    # Ingest event
    req = {"type": "QUOTE_INGESTED", "payload": {"foo": 1}}
    resp1 = client.post(f"/api/v2/sessions/{session_id}/events", json=req)
    v1 = resp1.json()["state_version"]
    applied1 = resp1.json()["applied"]
    # Ingest same event_id again
    event_id = resp1.json()["session_id"] + "-evt"
    req2 = {"event_id": event_id, "type": "QUOTE_INGESTED", "payload": {"foo": 1}}
    resp2 = client.post(f"/api/v2/sessions/{session_id}/events", json=req2)
    resp3 = client.post(f"/api/v2/sessions/{session_id}/events", json=req2)
    v2 = resp3.json()["state_version"]
    applied2 = resp3.json()["applied"]
    assert v2 == v1 + 1
    assert applied2 is False


def test_snapshot_determinism():
    resp = client.post("/api/v2/sessions")
    session_id = resp.json()["session_id"]
    reqs = [
        {"type": "QUOTE_INGESTED", "payload": {"val": i}} for i in range(3)
    ]
    for req in reqs:
        client.post(f"/api/v2/sessions/{session_id}/events", json=req)
    snap1 = client.get(f"/api/v2/sessions/{session_id}/snapshot")
    assert snap1.status_code == 200, f"snapshot1 failed: {snap1.status_code} body={snap1.text}"
    snap2 = client.get(f"/api/v2/sessions/{session_id}/snapshot")
    assert snap2.status_code == 200, f"snapshot2 failed: {snap2.status_code} body={snap2.text}"
    assert snap1.json()["state_hash"] == snap2.json()["state_hash"]
    assert snap1.json()["version"] == snap2.json()["version"]


def test_unknown_session_snapshot():
    resp = client.get("/api/v2/sessions/doesnotexist/snapshot")
    assert resp.status_code == 404
    assert "X-Correlation-Id" in resp.headers


def test_ordering_stability():
    # Forward order
    resp = client.post("/api/v2/sessions")
    session_id1 = resp.json()["session_id"]
    ts = "2025-01-01T12:00:00Z"
    e1 = {"event_id": "a", "type": "QUOTE_INGESTED", "ts": ts, "payload": {"foo": 1}}
    e2 = {"event_id": "b", "type": "QUOTE_INGESTED", "ts": ts, "payload": {"foo": 2}}
    client.post(f"/api/v2/sessions/{session_id1}/events", json=e1)
    client.post(f"/api/v2/sessions/{session_id1}/events", json=e2)
    snap1 = client.get(f"/api/v2/sessions/{session_id1}/snapshot").json()
    # Reverse order
    resp = client.post("/api/v2/sessions")
    session_id2 = resp.json()["session_id"]
    client.post(f"/api/v2/sessions/{session_id2}/events", json=e2)
    client.post(f"/api/v2/sessions/{session_id2}/events", json=e1)
    snap2 = client.get(f"/api/v2/sessions/{session_id2}/snapshot").json()
    assert snap1["state_hash"] == snap2["state_hash"]
    assert snap1["version"] == snap2["version"]


def test_404_correlation_id_provided():
    resp = client.get(
        "/api/v2/sessions/does-not-exist/snapshot",
        headers={"X-Correlation-Id": "cid-404"},
    )
    assert resp.status_code == 404
    assert resp.headers["X-Correlation-Id"] == "cid-404"
    # Error body unchanged
    assert resp.json() == {
        "detail": {
            "category": "NOT_FOUND",
            "code": "session_not_found",
            "message": "Session not found",
            "details": {},
            "error_count": 1,
        }
    }


def test_404_correlation_id_autogen():
    resp = client.get("/api/v2/sessions/does-not-exist/snapshot")
    assert resp.status_code == 404
    assert "X-Correlation-Id" in resp.headers
    assert resp.headers["X-Correlation-Id"]
    # Error body unchanged
    assert resp.json() == {
        "detail": {
            "category": "NOT_FOUND",
            "code": "session_not_found",
            "message": "Session not found",
            "details": {},
            "error_count": 1,
        }
    }


def test_v1_404_no_correlation_id():
    resp = client.get("/api/v1/doesnotexist")
    assert resp.status_code == 404
    assert "X-Correlation-Id" not in resp.headers
