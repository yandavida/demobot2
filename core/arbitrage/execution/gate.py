from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Iterable, Sequence

from core.arbitrage.models import ArbitrageOpportunity, VenueQuote


class ExecutionDecisionReason(str, Enum):
    EDGE_TOO_SMALL = "EDGE_TOO_SMALL"
    QUOTE_TOO_OLD = "QUOTE_TOO_OLD"
    SPREAD_TOO_WIDE = "SPREAD_TOO_WIDE"
    NOTIONAL_TOO_LARGE = "NOTIONAL_TOO_LARGE"
    PASS = "PASS"


@dataclass(frozen=True)
class ExecutionConstraints:
    min_edge_bps: float = 0.0
    max_quote_age_ms: float | None = None
    max_spread_bps: float | None = None
    max_notional: float | None = None


@dataclass(frozen=True)
class ExecutionDecision:
    reason: ExecutionDecisionReason
    edge_bps: float
    worst_spread_bps: float | None
    age_ms: float | None
    notional: float
    recommended_qty: float

    @property
    def should_execute(self) -> bool:
        return self.reason is ExecutionDecisionReason.PASS


def _resolve_as_of(opportunity: ArbitrageOpportunity, quotes: Iterable[VenueQuote | object]) -> datetime | None:
    if opportunity.as_of:
        return opportunity.as_of

    # Support quote containers that carry their own timestamps
    for q in quotes:
        as_of = getattr(q, "as_of", None)
        if as_of:
            return as_of

    return None


def _compute_worst_spread_bps(quotes: Sequence[VenueQuote]) -> float | None:
    spreads: list[float] = []
    for quote in quotes:
        bid, ask = quote.bid, quote.ask
        if bid is None or ask is None or bid <= 0 or ask <= 0:
            continue
        mid = (bid + ask) / 2
        if mid == 0:
            continue
        spreads.append(((ask - bid) / mid) * 10_000)

    if not spreads:
        return None

    return max(spreads)


def evaluate_execution_readiness(
    opportunity: ArbitrageOpportunity,
    quotes: Sequence[VenueQuote],
    constraints: ExecutionConstraints,
    now: datetime,
) -> ExecutionDecision:
    """Deterministically evaluate whether an opportunity is safe to execute."""

    edge_bps = opportunity.edge_bps
    worst_spread_bps = _compute_worst_spread_bps(quotes)
    as_of = _resolve_as_of(opportunity, quotes)
    age_ms: float | None = None
    if as_of is not None:
        age_ms = (now - as_of).total_seconds() * 1000

    notional = opportunity.buy.price * opportunity.size
    recommended_qty = opportunity.size

    if edge_bps < constraints.min_edge_bps:
        return ExecutionDecision(
            reason=ExecutionDecisionReason.EDGE_TOO_SMALL,
            edge_bps=edge_bps,
            worst_spread_bps=worst_spread_bps,
            age_ms=age_ms,
            notional=notional,
            recommended_qty=recommended_qty,
        )

    if constraints.max_quote_age_ms is not None:
        if age_ms is None or age_ms > constraints.max_quote_age_ms:
            return ExecutionDecision(
                reason=ExecutionDecisionReason.QUOTE_TOO_OLD,
                edge_bps=edge_bps,
                worst_spread_bps=worst_spread_bps,
                age_ms=age_ms,
                notional=notional,
                recommended_qty=recommended_qty,
            )

    if constraints.max_spread_bps is not None:
        if worst_spread_bps is None or worst_spread_bps > constraints.max_spread_bps:
            return ExecutionDecision(
                reason=ExecutionDecisionReason.SPREAD_TOO_WIDE,
                edge_bps=edge_bps,
                worst_spread_bps=worst_spread_bps,
                age_ms=age_ms,
                notional=notional,
                recommended_qty=recommended_qty,
            )

    if constraints.max_notional is not None and notional > constraints.max_notional:
        price = opportunity.buy.price
        recommended_qty = constraints.max_notional / price if price > 0 else 0.0
        return ExecutionDecision(
            reason=ExecutionDecisionReason.NOTIONAL_TOO_LARGE,
            edge_bps=edge_bps,
            worst_spread_bps=worst_spread_bps,
            age_ms=age_ms,
            notional=notional,
            recommended_qty=recommended_qty,
        )

    return ExecutionDecision(
        reason=ExecutionDecisionReason.PASS,
        edge_bps=edge_bps,
        worst_spread_bps=worst_spread_bps,
        age_ms=age_ms,
        notional=notional,
        recommended_qty=recommended_qty,
    )


__all__ = [
    "ExecutionDecision",
    "ExecutionDecisionReason",
    "ExecutionConstraints",
    "evaluate_execution_readiness",
]
