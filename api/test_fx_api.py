# tests/api/test_fx_api.py
from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)
API_KEY = "DEMOBOT_API_KEY"


def test_fx_analysis_basic() -> None:
    payload = {
        "base_ccy": "USD",
        "quote_ccy": "ILS",
        "notional": 1_000_000,
        "tenor_days": 90,
        "hedge_ratio": 1.0,
    }

    resp = client.post(
        "/v1/fx/forward/analyze",
        json=payload,
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
