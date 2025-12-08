# tests/api/test_strategy_api.py
from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

API_KEY = "DEMOBOT_API_KEY"  # אותו key כמו ב־env/dev שלך


def test_strategy_suggest_ok() -> None:
    payload = {
        "underlying": "SPX",
        "spot": 5000.0,
        "goal": "income",
        "risk_profile": "medium",
        "days_to_expiry": 30,
    }

    resp = client.post(
        "/v1/strategy/suggest",
        json=payload,
        headers={"X-API-Key": API_KEY},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "strategies" in data
    assert isinstance(data["strategies"], list)


def test_strategy_suggest_unauthorized() -> None:
    payload = {
        "underlying": "SPX",
        "spot": 5000.0,
        "goal": "income",
        "risk_profile": "medium",
        "days_to_expiry": 30,
    }

    resp = client.post("/v1/strategy/suggest", json=payload)
    assert resp.status_code in (401, 403)
