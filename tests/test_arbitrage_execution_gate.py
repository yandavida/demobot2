from datetime import datetime, timedelta

import pytest

from core.arbitrage.execution.gate import (
    ExecutionConstraints,
    ExecutionDecisionReason,
    evaluate_execution_readiness,
)
from core.arbitrage.models import ArbitrageLeg, ArbitrageOpportunity, VenueQuote


NOW = datetime(2024, 1, 1, 12, 0, 0)


def _build_opportunity(**overrides) -> ArbitrageOpportunity:
    base = dict(
        symbol="XYZ",
        buy=ArbitrageLeg(action="buy", venue="Alpha", price=99.5, quantity=5),
        sell=ArbitrageLeg(action="sell", venue="Bravo", price=100.5, quantity=5),
        gross_edge=1.0,
        net_edge=1.0,
        edge_bps=(1.0 / 99.5) * 10_000,
        size=5,
        as_of=NOW - timedelta(seconds=1),
    )
    base.update(overrides)
    return ArbitrageOpportunity(**base)


def _quotes_with_spread(bid: float, ask: float) -> list[VenueQuote]:
    return [
        VenueQuote(venue="Alpha", symbol="XYZ", bid=bid, ask=ask, size=10),
        VenueQuote(venue="Bravo", symbol="XYZ", bid=bid + 1, ask=ask + 1, size=10),
    ]


def test_passes_when_all_constraints_met():
    opportunity = _build_opportunity()
    quotes = _quotes_with_spread(99.4, 99.5)
    constraints = ExecutionConstraints(
        min_edge_bps=50,
        max_quote_age_ms=2_000,
        max_spread_bps=20,
        max_notional=1_000,
    )

    decision = evaluate_execution_readiness(opportunity, quotes, constraints, NOW)

    assert decision.reason is ExecutionDecisionReason.PASS
    assert decision.should_execute is True
    assert decision.edge_bps == opportunity.edge_bps
    assert decision.worst_spread_bps is not None and decision.worst_spread_bps < 20
    assert decision.age_ms is not None and decision.age_ms <= 2_000
    assert decision.notional == pytest.approx(opportunity.buy.price * opportunity.size)
    assert decision.recommended_qty == opportunity.size


def test_rejects_small_edge_first():
    opportunity = _build_opportunity(edge_bps=10)
    quotes = _quotes_with_spread(99.4, 99.5)
    constraints = ExecutionConstraints(min_edge_bps=50)

    decision = evaluate_execution_readiness(opportunity, quotes, constraints, NOW)

    assert decision.reason is ExecutionDecisionReason.EDGE_TOO_SMALL


def test_rejects_old_quotes_conservatively():
    opportunity = _build_opportunity(as_of=NOW - timedelta(seconds=10))
    quotes = _quotes_with_spread(99.4, 99.5)
    constraints = ExecutionConstraints(min_edge_bps=50, max_quote_age_ms=1_000)

    decision = evaluate_execution_readiness(opportunity, quotes, constraints, NOW)

    assert decision.reason is ExecutionDecisionReason.QUOTE_TOO_OLD


def test_rejects_spread_too_wide():
    opportunity = _build_opportunity()
    quotes = _quotes_with_spread(100.0, 102.0)
    constraints = ExecutionConstraints(min_edge_bps=50, max_spread_bps=50)

    decision = evaluate_execution_readiness(opportunity, quotes, constraints, NOW)

    assert decision.reason is ExecutionDecisionReason.SPREAD_TOO_WIDE


def test_rejects_notional_too_large_with_recommended_qty():
    opportunity = _build_opportunity(size=20, buy=_build_opportunity().buy)
    quotes = _quotes_with_spread(99.4, 99.5)
    constraints = ExecutionConstraints(min_edge_bps=50, max_notional=500)

    decision = evaluate_execution_readiness(opportunity, quotes, constraints, NOW)

    assert decision.reason is ExecutionDecisionReason.NOTIONAL_TOO_LARGE
    assert decision.notional == pytest.approx(opportunity.buy.price * opportunity.size)
    assert decision.recommended_qty == pytest.approx(500 / opportunity.buy.price)


def test_deterministic_output():
    opportunity = _build_opportunity()
    quotes = _quotes_with_spread(99.4, 99.5)
    constraints = ExecutionConstraints(min_edge_bps=50)

    first = evaluate_execution_readiness(opportunity, quotes, constraints, NOW)
    second = evaluate_execution_readiness(opportunity, quotes, constraints, NOW)

    assert first == second
