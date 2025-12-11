# tests/ui/test_api_client.py
from __future__ import annotations

from typing import Any, Dict

import pytest

from ui import api_client
from ui.api_client import ApiError


class DummyResponse:
    def __init__(self, status_code: int, json_data: Dict[str, Any] | None = None):
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self) -> Dict[str, Any]:
        return self._json_data

    @property
    def text(self) -> str:
        return str(self._json_data)


def test_request_json_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(method: str, url: str, **kwargs: Any) -> DummyResponse:
        return DummyResponse(200, {"ok": True})

    monkeypatch.setattr(api_client.requests, "request", fake_request)

    data = api_client._request_json("GET", "/health")
    assert data == {"ok": True}


def test_request_json_raises_api_error_on_401(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(method: str, url: str, **kwargs: Any) -> DummyResponse:
        return DummyResponse(401, {"detail": "Unauthorized"})

    monkeypatch.setattr(api_client.requests, "request", fake_request)

    with pytest.raises(ApiError) as exc:
        api_client._request_json("GET", "/v1/strategy/suggest")

    err = exc.value
    assert err.status_code == 401
    assert err.error_type == "auth"


def test_valuate_portfolio_uses_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: Dict[str, Any] = {}

    def fake_request_json(method: str, path: str, json: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        captured.update({"method": method, "path": path, "json": json, "timeout": timeout})
        return {"total_value": 10_000.0, "currency": "ILS"}

    monkeypatch.setattr(api_client, "_request_json", fake_request_json)

    positions = [
        {
            "symbol": "AAPL",
            "quantity": 2,
            "price": 170.0,
            "currency": "USD",
            "instrument_type": "equity",
        }
    ]

    response = api_client.valuate_portfolio(positions=positions)

    assert response["total_value"] == 10_000.0
    assert captured["path"] == "/v1/portfolio/valuate"
    assert captured["timeout"] == 30
    assert captured["json"]["positions"] == positions
    assert captured["json"]["base_currency"] == api_client.DEFAULT_BASE_CURRENCY
    assert captured["json"]["fx_rates"] == dict(api_client.DEFAULT_FX_RATES)


def test_valuate_portfolio_overrides_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: Dict[str, Any] = {}

    def fake_request_json(method: str, path: str, json: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        captured.update({"method": method, "path": path, "json": json, "timeout": timeout})
        return {"total_value": 5_000.0, "currency": "EUR"}

    monkeypatch.setattr(api_client, "_request_json", fake_request_json)

    positions = [
        {
            "symbol": "MSFT",
            "quantity": 1,
            "price": 330.0,
            "currency": "EUR",
            "instrument_type": "equity",
        }
    ]

    custom_fx = {"EUR/USD": 1.1, "USD/EUR": 0.91}

    response = api_client.valuate_portfolio(
        positions=positions,
        base_currency="EUR",
        fx_rates=custom_fx,
    )

    assert response["currency"] == "EUR"
    assert captured["json"]["base_currency"] == "EUR"
    assert captured["json"]["fx_rates"] == custom_fx
