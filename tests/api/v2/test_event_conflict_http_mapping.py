import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.v2.service import reset_for_tests

client = TestClient(app, raise_server_exceptions=True)


@pytest.fixture(autouse=True)
def reset_service():
    reset_for_tests()


def test_event_conflict_mapped_to_409():
    # create session
    resp = client.post("/api/v2/sessions")
    assert resp.status_code == 201
    session_id = resp.json()["session_id"]

    # ingest initial event
    req = {"event_id": "dup-1", "type": "QUOTE_INGESTED", "payload": {"v": 1}}
    r1 = client.post(f"/api/v2/sessions/{session_id}/events", json=req)
    assert r1.status_code == 201

    # ingest conflicting event with same event_id but different payload -> should 409
    req2 = {"event_id": "dup-1", "type": "QUOTE_INGESTED", "payload": {"v": 2}}
    r2 = client.post(f"/api/v2/sessions/{session_id}/events", json=req2)
    assert r2.status_code == 409

    body = r2.json()
    assert isinstance(body, dict) and "detail" in body
    detail = body["detail"]
    assert detail.get("code") == "event_conflict"
    assert detail.get("category") == "CONFLICT"
    assert detail.get("message")
    assert isinstance(detail.get("details"), dict)
    assert detail["details"].get("reason") == "conflicting event payload for existing event_id"
    assert detail["details"].get("event_id") == "dup-1"
    # regression: ensure not a 500
    assert r2.status_code != 500
