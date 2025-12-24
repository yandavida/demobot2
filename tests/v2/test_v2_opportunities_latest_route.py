from fastapi.testclient import TestClient
from api.main import app

def test_latest_opportunities_route():
    client = TestClient(app)
    # יצירת session
    resp = client.post("/api/v2/sessions")
    assert resp.status_code == 201
    session_id = resp.json()["session_id"]
    # הזנת quotes בסיסיים (simulate minimal ingest)
    quote_payload = {"bid": 3.5, "ask": 3.6}
    cmd = {"type": "QUOTE_INGESTED", "payload": quote_payload}
    resp_evt = client.post(f"/api/v2/sessions/{session_id}/events", json=cmd)
    assert resp_evt.status_code == 201
    # קריאה ל-latest opportunities
    resp = client.get(f"/api/v2/opportunities/latest?session_id={session_id}&limit=10")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert isinstance(body["items"], list)
    # בדיקת מבנה של כל item
    for item in body["items"]:
        for key in ["opportunity_id", "symbol", "buy_venue", "sell_venue", "prices", "decision_trace"]:
            assert key in item
        dt = item["decision_trace"]
        assert set(dt.keys()) == {"verdict", "reasons", "metrics"}
        assert dt["verdict"] in ("ACCEPTED", "REJECTED")
        assert isinstance(dt["reasons"], list)
        assert isinstance(dt["metrics"], list)

# בדיקת דטרמיניזם בסיסית
import copy

def test_latest_opportunities_determinism():
    client = TestClient(app)
    resp = client.post("/api/v2/sessions")
    session_id = resp.json()["session_id"]
    # הזנת quotes בסדר שונה
    quotes1 = [
        {"bid": 3.5, "ask": 3.6},
        {"bid": 3.4, "ask": 3.7},
    ]
    quotes2 = list(reversed(quotes1))
    for q in quotes1:
        client.post(f"/api/v2/sessions/{session_id}/events", json={"type": "QUOTE_INGESTED", "payload": q})
    resp1 = client.get(f"/api/v2/opportunities/latest?session_id={session_id}&limit=10")
    items1 = copy.deepcopy(resp1.json()["items"])
    # יצירת session חדש והזנה בסדר הפוך
    resp = client.post("/api/v2/sessions")
    session_id2 = resp.json()["session_id"]
    for q in quotes2:
        client.post(f"/api/v2/sessions/{session_id2}/events", json={"type": "QUOTE_INGESTED", "payload": q})
    resp2 = client.get(f"/api/v2/opportunities/latest?session_id={session_id2}&limit=10")
    items2 = copy.deepcopy(resp2.json()["items"])
    # assert דטרמיניזם: התוצאה זהה אחרי מיון
    def sort_items(items):
        return sorted(items, key=lambda o: (o["symbol"], o["buy_venue"], o["sell_venue"], o["prices"]["buy_ask"], o["prices"]["sell_bid"], o["opportunity_id"]))
    assert sort_items(items1) == sort_items(items2)
