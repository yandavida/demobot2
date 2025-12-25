
from fastapi.testclient import TestClient
from api.main import app

def test_portfolio_event_types_ingest():
    client = TestClient(app)
    # Create session
    resp = client.post("/api/v2/sessions")
    assert resp.status_code == 201
    session_id = resp.json()["session_id"]

    events = [
        {
            "type": "PORTFOLIO_CREATED",
            "event_id": "evt-portfolio-created-1",
            "payload": {"portfolio": {"name": "test"}},
        },
        {
            "type": "PORTFOLIO_POSITION_UPSERTED",
            "event_id": "evt-pos-upsert-1",
            "payload": {"position": {"id": "p1", "qty": 10}},
        },
        {
            "type": "PORTFOLIO_POSITION_REMOVED",
            "event_id": "evt-pos-remove-1",
            "payload": {"position_id": "p1"},
        },
    ]
    for event in events:
        r = client.post(f"/api/v2/sessions/{session_id}/events", json=event)
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["applied"] is True
        # Idempotency: re-ingest same event_id
        r2 = client.post(f"/api/v2/sessions/{session_id}/events", json=event)
        assert r2.status_code == 201, r2.text
        data2 = r2.json()
        assert data2["applied"] is False
