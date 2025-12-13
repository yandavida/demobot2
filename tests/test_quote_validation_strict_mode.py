import pytest
from fastapi import HTTPException

from api.v1.arbitrage_orch import ScanRequest, scan
from core.arbitrage.models import ArbitrageConfig
from core.services.arbitrage_orchestration import create_arbitrage_session


def _build_request(strict_validation: bool) -> ScanRequest:
    session_id = create_arbitrage_session(
        base_currency="USD", config=ArbitrageConfig(min_edge_bps=0)
    )
    return ScanRequest(
        session_id=session_id,
        fx_rate_usd_ils=3.5,
        strict_validation=strict_validation,
        quotes=[{"symbol": "ES", "venue": "EX_A", "bid": None, "ask": None}],
    )


def test_scan_strict_validation_rejects_invalid_quotes() -> None:
    req = _build_request(strict_validation=True)

    with pytest.raises(HTTPException) as exc_info:
        scan(req)

    assert exc_info.value.status_code == 400
    detail = exc_info.value.detail
    assert detail["errors"]
    assert detail["error_count"] == len(detail["errors"])


def test_scan_non_strict_includes_validation_summary() -> None:
    req = _build_request(strict_validation=False)
    response = scan(req)

    assert response.validation_summary is not None
    assert response.validation_summary.error_count >= 1
    assert response.opportunities == []
