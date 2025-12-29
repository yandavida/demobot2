import traceback
from fastapi.testclient import TestClient
from api.main import app

def main():
    client = TestClient(app, raise_server_exceptions=True)
    sid = client.post("/api/v2/sessions").json()["session_id"]
    for i in range(3):
        client.post(f"/api/v2/sessions/{sid}/events", json={"type": "QUOTE_INGESTED", "payload": {"val": i}})
    print("First GET /snapshot:")
    resp1 = client.get(f"/api/v2/sessions/{sid}/snapshot")
    print("Status:", resp1.status_code)
    print("Body:", resp1.json())
    print("Second GET /snapshot (should raise):")
    try:
        resp2 = client.get(f"/api/v2/sessions/{sid}/snapshot")
        print("Status:", resp2.status_code)
        print("Body:", resp2.json())
    except Exception:
        print("Exception on second GET:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
