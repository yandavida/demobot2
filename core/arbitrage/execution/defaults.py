from __future__ import annotations

from core.arbitrage.execution.gate import ExecutionConstraints
from core.portfolio.models import Currency, Money


# Conservative defaults intended to keep the execution layer on the safe side
# until tuned with production telemetry. Values err on the side of caution to
# avoid firing on noisy or stale signals.
_DEFAULT_MIN_EDGE_BPS = 35.0  # Require at least 35 bps of edge before executing
_DEFAULT_MIN_EXPECTED_PROFIT = 10.0  # 10 units of base currency per trade
_DEFAULT_MIN_SIZE = 1.0  # Avoid dust trades
_DEFAULT_MAX_AGE_MS = 1500  # Do not execute on quotes older than ~1.5 seconds
_DEFAULT_MAX_TOTAL_LATENCY_MS = 500  # Cap round-trip venue latency budget to 0.5s


def default_execution_constraints(base_currency: Currency = "ILS") -> ExecutionConstraints:
    """Return a single source of truth for execution gate thresholds.

    The defaults are intentionally conservative. They aim to protect capital
    while we gather real-world performance data and can tighten or loosen the
    gate based on evidence.
    """

    min_expected_profit = Money(
        amount=_DEFAULT_MIN_EXPECTED_PROFIT,
        ccy=base_currency,
    )

    return ExecutionConstraints(
        base_currency=base_currency,
        min_edge_bps=_DEFAULT_MIN_EDGE_BPS,
        min_expected_profit=min_expected_profit,
        min_size=_DEFAULT_MIN_SIZE,
        max_age_ms=_DEFAULT_MAX_AGE_MS,
        max_total_latency_ms=_DEFAULT_MAX_TOTAL_LATENCY_MS,
    )
