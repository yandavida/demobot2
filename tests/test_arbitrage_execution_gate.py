from datetime import datetime, timedelta

from core.arbitrage.execution import (
    ExecutionConstraints,
    default_execution_constraints,
    is_actionable,
)
from core.arbitrage.models import ArbitrageLeg, ArbitrageOpportunity


def _make_opportunity(*, edge_bps: float, net_edge: float, size: float, as_of: datetime) -> ArbitrageOpportunity:
    buy_leg = ArbitrageLeg(action="buy", venue="Alpha", price=100.0, quantity=size, ccy="ILS")
    sell_leg = ArbitrageLeg(action="sell", venue="Bravo", price=101.0, quantity=size, ccy="ILS")
    return ArbitrageOpportunity(
        symbol="XYZ",
        buy=buy_leg,
        sell=sell_leg,
        gross_edge=1.0,
        net_edge=net_edge,
        edge_bps=edge_bps,
        size=size,
        ccy="ILS",
        as_of=as_of,
    )


def test_default_execution_constraints_are_conservative() -> None:
    constraints = default_execution_constraints()

    assert isinstance(constraints, ExecutionConstraints)
    assert constraints.base_currency == "ILS"
    assert constraints.min_edge_bps > 0
    assert constraints.min_size >= 1
    assert 0 < constraints.max_age_ms <= 2_000
    assert 0 < constraints.max_total_latency_ms <= 1_000
    assert constraints.min_expected_profit.amount > 0
    assert constraints.min_expected_profit.ccy == "ILS"


def test_default_execution_constraints_respects_base_currency() -> None:
    constraints = default_execution_constraints(base_currency="USD")

    assert constraints.base_currency == "USD"
    assert constraints.min_expected_profit.ccy == "USD"


def test_is_actionable_respects_thresholds() -> None:
    constraints = default_execution_constraints()
    opp = _make_opportunity(
        edge_bps=constraints.min_edge_bps + 5,
        net_edge=constraints.min_expected_profit.amount,
        size=max(constraints.min_size, 1.0),
        as_of=datetime.utcnow(),
    )

    assert is_actionable(opp, constraints)


def test_is_actionable_rejects_stale_opportunities() -> None:
    constraints = default_execution_constraints()
    now = datetime.utcnow()
    stale_as_of = now - timedelta(milliseconds=constraints.max_age_ms + 10)
    opp = _make_opportunity(
        edge_bps=constraints.min_edge_bps + 5,
        net_edge=constraints.min_expected_profit.amount,
        size=max(constraints.min_size, 1.0),
        as_of=stale_as_of,
    )

    assert not is_actionable(opp, constraints, as_of=now)
