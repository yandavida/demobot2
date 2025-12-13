from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.arbitrage.models import ArbitrageOpportunity
from core.portfolio.models import Currency, Money


@dataclass(frozen=True)
class ExecutionConstraints:
    """Basic risk/quality guardrails for sending arbitrage orders.

    Attributes:
        base_currency: Portfolio base currency used for monetary thresholds.
        min_edge_bps: Minimum edge in basis points required to consider execution.
        min_expected_profit: Minimum expected absolute profit in base currency.
        min_size: Minimum trade size to avoid dust orders.
        max_age_ms: Maximum opportunity staleness (ms) allowed since detection.
        max_total_latency_ms: Maximum acceptable latency budget across venues (ms).
    """

    base_currency: Currency
    min_edge_bps: float
    min_expected_profit: Money
    min_size: float
    max_age_ms: int
    max_total_latency_ms: int


def is_actionable(
    opportunity: ArbitrageOpportunity,
    constraints: ExecutionConstraints,
    *,
    as_of: datetime | None = None,
) -> bool:
    """Return True if the opportunity meets the execution guardrails.

    This helper intentionally keeps the policy light-weight; callers can layer
    additional broker- or venue-specific checks as needed.
    """

    if opportunity.edge_bps < constraints.min_edge_bps:
        return False

    if opportunity.size < constraints.min_size:
        return False

    if opportunity.net_edge * opportunity.size < constraints.min_expected_profit.amount:
        return False

    now = as_of or datetime.utcnow()
    if opportunity.as_of:
        age_ms = (now - opportunity.as_of).total_seconds() * 1000
        if age_ms > constraints.max_age_ms:
            return False

    latencies = [
        latency
        for latency in (
            getattr(opportunity.buy, "latency_ms", None),
            getattr(opportunity.sell, "latency_ms", None),
        )
        if latency is not None
    ]
    if latencies and sum(latencies) > constraints.max_total_latency_ms:
        return False

    return True
