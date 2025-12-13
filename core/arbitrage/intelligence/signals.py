from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Iterable

from core.arbitrage.intelligence.lifecycle import OpportunityState

if TYPE_CHECKING:  # pragma: no cover
    from core.arbitrage.orchestrator import OpportunityRecord


@dataclass
class OpportunitySignals:
    opportunity_id: str
    values: Dict[str, float]


def compute_signals(
    opportunity: OpportunityRecord,
    state: OpportunityState,
    now: datetime,
    history: Iterable[OpportunityRecord],
) -> OpportunitySignals:
    age_seconds = (now - state.first_seen).total_seconds()
    freshness_ms = (now - state.last_seen).total_seconds() * 1000

    # naive stability: compare last two edges if available
    past_edges = [op.opportunity.edge_bps for op in history if op.opportunity.opportunity_id == state.opportunity_id]
    stability = 1.0
    if len(past_edges) >= 2:
        last = past_edges[-1]
        prev = past_edges[-2]
        if last != 0:
            stability = 1 - abs(last - prev) / abs(last)

    values: Dict[str, float] = {
        "freshness_ms": freshness_ms,
        "seen_count": float(state.seen_count),
        "age_seconds": age_seconds,
        "edge_bps_current": opportunity.opportunity.edge_bps,
        "edge_bps_stability": stability,
        "net_edge_bps": opportunity.opportunity.net_edge,
    }
    return OpportunitySignals(opportunity_id=state.opportunity_id, values=values)


__all__ = ["compute_signals", "OpportunitySignals"]
