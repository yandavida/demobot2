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
