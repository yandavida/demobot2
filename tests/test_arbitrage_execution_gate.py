from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from core.arbitrage.execution.defaults import default_execution_constraints
from core.arbitrage.execution.gate import evaluate_execution_readiness
from core.arbitrage.execution.models import ExecutionConstraints
from core.arbitrage.execution import reasons


def _now() -> datetime:
    return datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def _quotes(now: datetime, *, bid: float = 99.0, ask: float = 101.0, age_ms: int = 10) -> dict[str, dict]:
    return {
        "V1": {"bid": bid, "ask": ask, "ts": now - timedelta(milliseconds=age_ms)},
        "V2": {"bid": bid, "ask": ask, "ts": now - timedelta(milliseconds=age_ms)},
    }


def _constraints() -> ExecutionConstraints:
    # Small helper for deterministic tests (not defaults)
    return ExecutionConstraints(
        min_edge_bps=5.0,
        max_spread_bps=50.0,
        max_age_ms=200.0,
        max_notional=10_000.0,
        max_quantity=100.0,
        max_latency_ms=250.0,
        allowed_venues=None,
        conservative_by_default=True,
    )


def test_default_execution_constraints_are_conservative() -> None:
    c = default_execution_constraints()

    assert isinstance(c, ExecutionConstraints)
    # Conservative sanity (no magic numbers in tests; just invariants)
    assert c.min_edge_bps > 0
    assert 0 < c.max_age_ms <= 5_000
    assert 0 < c.max_spread_bps <= 1_000
    assert c.max_notional > 0
    assert c.max_quantity > 0
    assert c.max_latency_ms > 0
    assert c.conservative_by_default is True


def test_pass_case() -> None:
    now = _now()
    opp = {"edge_bps": 10.0, "quantity": 10.0, "venue": "V1", "latency_ms": 100.0}
    q = _quotes(now, bid=99.5, ask=100.5, age_ms=50)

    d = evaluate_execution_readiness(opp, q, _constraints(), now)

    assert d.can_execute is True
    assert d.reason_codes == []
    assert d.metrics["edge_bps"] == pytest.approx(10.0)
    assert d.metrics["worst_spread_bps"] <= 50.0
    assert d.metrics["age_ms"] <= 200.0
    assert d.recommended_qty > 0


def test_edge_too_small() -> None:
    now = _now()
    opp = {"edge_bps": 1.0, "quantity": 10.0}
    d = evaluate_execution_readiness(opp, _quotes(now), _constraints(), now)

    assert d.can_execute is False
    assert reasons.EDGE_TOO_SMALL in d.reason_codes


def test_quote_too_old() -> None:
    now = _now()
    opp = {"edge_bps": 10.0, "quantity": 10.0}
    d = evaluate_execution_readiness(opp, _quotes(now, age_ms=500), _constraints(), now)

    assert d.can_execute is False
    assert reasons.QUOTE_TOO_OLD in d.reason_codes


def test_spread_too_wide() -> None:
    now = _now()
    opp = {"edge_bps": 10.0, "quantity": 10.0}
    d = evaluate_execution_readiness(opp, _quotes(now, bid=90.0, ask=110.0, age_ms=50), _constraints(), now)

    assert d.can_execute is False
    assert reasons.SPREAD_TOO_WIDE in d.reason_codes


def test_notional_or_qty_too_large() -> None:
    now = _now()
    opp = {"edge_bps": 10.0, "quantity": 200.0}  # max_quantity=100 -> fail-fast
    d = evaluate_execution_readiness(opp, _quotes(now, bid=99.0, ask=101.0, age_ms=50), _constraints(), now)

    assert d.can_execute is False
    assert any(rc in d.reason_codes for rc in [reasons.QTY_TOO_LARGE, reasons.NOTIONAL_TOO_LARGE])


def test_determinism_same_input_same_output() -> None:
    now = _now()
    opp = {"edge_bps": 12.0, "quantity": 10.0, "venue": "V1", "latency_ms": 100.0}
    q = _quotes(now, bid=99.5, ask=100.5, age_ms=50)
    c = _constraints()

    d1 = evaluate_execution_readiness(opp, q, c, now)
    d2 = evaluate_execution_readiness(opp, q, c, now)

    assert d1.can_execute == d2.can_execute
    assert d1.reason_codes == d2.reason_codes
    assert d1.metrics == d2.metrics
    assert d1.recommended_qty == pytest.approx(d2.recommended_qty)
    assert d1.ts == d2.ts
