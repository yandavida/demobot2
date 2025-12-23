from fastapi.testclient import TestClient
from api.main import app
from api.v2.commands import QuoteIngestCommand

client = TestClient(app)

# Helper to create a session
def create_session():
    resp = client.post("/api/v2/sessions")
    assert resp.status_code == 201
    return resp.json()["session_id"]

# Happy path test for QUOTE_INGESTED with valid payload
def test_quote_ingest_command_happy_path():
    session_id = create_session()
    cmd = QuoteIngestCommand(payload={"bid": 1.23, "ask": 1.25})
    resp = client.post(f"/api/v2/sessions/{session_id}/events", json=cmd.model_dump())
    assert resp.status_code == 201
    data = resp.json()
    assert data["session_id"] == session_id
    assert data["applied"] is True
    assert isinstance(data["state_version"], int)

# Invalid: payload is not a dict
def test_quote_ingest_command_invalid_payload_type():
    session_id = create_session()
    bad_cmd = {"type": "QUOTE_INGESTED", "payload": "notadict"}
    resp = client.post(f"/api/v2/sessions/{session_id}/events", json=bad_cmd)
    # Pydantic validation error: payload must be a dict, so 422
    assert resp.status_code == 422
    assert "payload" in str(resp.json())

# Invalid: payload is empty
def test_quote_ingest_command_empty_payload():
    session_id = create_session()
    bad_cmd = {"type": "QUOTE_INGESTED", "payload": {}}
    resp = client.post(f"/api/v2/sessions/{session_id}/events", json=bad_cmd)
    assert resp.status_code == 400
    assert "payload must not be empty" in str(resp.json())

# Invalid: missing payload
def test_quote_ingest_command_missing_payload():
    session_id = create_session()
    bad_cmd = {"type": "QUOTE_INGESTED"}
    resp = client.post(f"/api/v2/sessions/{session_id}/events", json=bad_cmd)
    assert resp.status_code == 422  # Pydantic validation error
    assert "payload" in str(resp.json())
