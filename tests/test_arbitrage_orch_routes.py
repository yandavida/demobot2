import pytest
from fastapi import APIRouter

from api.v1.arbitrage_orch import (
    HistoryRequest,
    ScanRequest,
    check_route_collisions,
    history,
    router as arbitrage_router,
    scan,
)
from core.arbitrage.models import ArbitrageConfig
from core.services.arbitrage_orchestration import create_arbitrage_session


def test_check_route_collisions_detects_duplicates() -> None:
    router = APIRouter()

    @router.get("/duplicate")
    def first():
        return {"message": "first"}

    @router.get("/duplicate")
    def second():
        return {"message": "second"}

    with pytest.raises(ValueError):
        check_route_collisions(router)


def test_check_route_collisions_on_main_router_does_not_raise() -> None:
    # sanity: our main router should not have duplicates
    check_route_collisions(arbitrage_router)


def _build_scan_request() -> ScanRequest:
    session_id = create_arbitrage_session(
        base_currency="USD",
        config=ArbitrageConfig(min_edge_bps=0),
    )

    # Important: bid <= ask (valid market quotes)
    # And create a cross-venue opportunity:
    # Buy on EX_A at ask=100, sell on EX_B at bid=101  => positive edge.
    return ScanRequest(
        session_id=session_id,
        fx_rate_usd_ils=3.5,
        strict_validation=False,
        quotes=[
            {"symbol": "ES", "venue": "EX_A", "bid": 99.0, "ask": 100.0, "ccy": "USD"},
            {"symbol": "ES", "venue": "EX_B", "bid": 101.0, "ask": 102.0, "ccy": "USD"},
        ],
    )


def test_scan_response_includes_quote_validation() -> None:
    req = _build_scan_request()
    resp = scan(req)

    assert resp.quote_validation is not None, "Expected quote_validation to be present"
    assert resp.quote_validation.error_count == 0, "Expected no validation errors"
    assert resp.quote_validation.invalid in (0, None), "Expected no invalid quotes"

    assert resp.opportunities, "Expected at least one opportunity"


def test_history_endpoint_returns_opportunities_and_does_not_crash() -> None:
    req = _build_scan_request()
    _ = scan(req)

    hist = history(HistoryRequest(session_id=req.session_id, symbol="ES"))
    assert isinstance(hist, list)
    assert hist, "Expected history to contain opportunities"
