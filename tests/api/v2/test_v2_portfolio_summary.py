from api.main import app
from fastapi.testclient import TestClient
from core.v2.models import V2Event
def make_event(event_id, type, ts, payload):
    return V2Event(
        event_id=event_id,
        session_id="sess1",
        ts=ts,
        type=type,
        payload=payload,
        payload_hash="h",
    )

def setup_portfolio_events():
    ts0 = "2023-01-01T10:00:00Z"
    ts1 = "2023-01-01T10:01:00Z"
    base_payload = {"base_currency": "USD", "constraints": {"max_notional": 1000.0}}
    upsert_payload = {
        "position": {
            "position_id": "p1",
            "legs": [
                {
                    "leg_id": "l1",
                    "underlying": "AAPL",
                    "pv_per_unit": 1.0,
                    "greeks_per_unit": {"delta": 1.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0},
                    "notional_per_unit": 100.0,
                    "quantity": 10.0,
                }
            ],
        }
    }
    return [
        {"event_id": "e1", "type": "PORTFOLIO_CREATED", "ts": ts0, "payload": base_payload},
        {"event_id": "e2", "type": "PORTFOLIO_POSITION_UPSERTED", "ts": ts1, "payload": upsert_payload},
    ]

def test_portfolio_summary_endpoint():
    client = TestClient(app)
    # Create session
    resp = client.post("/api/v2/sessions")
    assert resp.status_code == 201
    session_id = resp.json()["session_id"]
    # Inject events directly
    # Ingest events via API
    for event in setup_portfolio_events():
        req = event.copy()
        r = client.post(f"/api/v2/sessions/{session_id}/events", json=req)
        assert r.status_code == 201, r.text
    # Call endpoint
    r = client.get(f"/api/v2/sessions/{session_id}/portfolio/summary")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["pv"]["value"] == 10.0
    assert data["delta"] == 10.0
    assert data["exposures"][0]["underlying"] == "AAPL"
    # Idempotency: duplicate event_id
    dup_event = setup_portfolio_events()[1]
    r2 = client.post(f"/api/v2/sessions/{session_id}/events", json=dup_event)
    assert r2.status_code == 201
    r2 = client.get(f"/api/v2/sessions/{session_id}/portfolio/summary")
    assert r2.status_code == 200
    assert r2.json() == data
