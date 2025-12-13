import pytest
from fastapi import APIRouter

from api.v1.arbitrage_orch import (
    HistoryRequest,
    OpportunitiesWithValidationResponse,
    ScanRequest,
    check_route_collisions,
    history,
    history_window,
    router as arbitrage_router,
    scan,
)
from core.arbitrage.models import ArbitrageConfig
from core.services.arbitrage_orchestration import create_arbitrage_session


def test_check_route_collisions_detects_duplicates():
    router = APIRouter()

    @router.get("/duplicate")
    def first():
        return {"message": "first"}

    @router.get("/duplicate")
    def second():
        return {"message": "second"}

    with pytest.raises(ValueError):
        check_route_collisions(router)


def _build_scan_request() -> ScanRequest:
    session_id = create_arbitrage_session(
        base_currency="USD", config=ArbitrageConfig(min_edge_bps=0)
    )
    return ScanRequest(
        session_id=session_id,
        fx_rate_usd_ils=3.5,
        quotes=[
            {"symbol": "ES", "venue": "EX_A", "bid": 100.0, "ask": 99.5},
            {"symbol": "ES", "venue": "EX_B", "bid": 101.0, "ask": 100.5},
        ],
    )


def test_scan_response_includes_validation_summary() -> None:
    scan_request = _build_scan_request()
    response = scan(scan_request)

    assert response.validation_summary is not None
    assert response.validation_summary.error_count == 0
    assert response.opportunities


def test_history_endpoints_propagate_validation_summary() -> None:
    scan_request = _build_scan_request()
    scan_response = scan(scan_request)
    assert scan_response.opportunities

    history_response = history(
        HistoryRequest(session_id=scan_request.session_id, symbol="ES")
    )
    assert isinstance(history_response, OpportunitiesWithValidationResponse)
    assert history_response.validation_summary is not None
    assert history_response.validation_summary.error_count == 0
    assert history_response.opportunities

    window_response = history_window(
        session_id=scan_request.session_id, symbol="ES", limit=5
    )
    assert isinstance(window_response, OpportunitiesWithValidationResponse)
    assert window_response.validation_summary is not None
    assert window_response.validation_summary.error_count == 0
    assert window_response.opportunities
