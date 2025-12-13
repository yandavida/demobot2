from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Iterable, List

from core.arbitrage.execution.gate import ExecutionDecision
from core.arbitrage.intelligence.reasons import Reason, classify_reasons
from core.arbitrage.intelligence.readiness import ExecutionReadiness
from core.arbitrage.intelligence.signals import OpportunitySignals

if TYPE_CHECKING:  # pragma: no cover
    from core.arbitrage.orchestrator import OpportunityRecord


@dataclass
class RankedRecommendation:
    opportunity_id: str
    rank: int
    quality_score: float
    reasons: List[Reason]
    signals: Dict[str, float]
    economics: dict[str, object]
    execution_readiness: ExecutionReadiness | None = None
    execution_decision: ExecutionDecision | None = None


def score_signals(signals: dict[str, float]) -> float:
    freshness = signals.get("freshness_ms", 0)
    stability = signals.get("edge_bps_stability", 1)
    net_edge = signals.get("net_edge_bps", 0)

    score = 0.0
    # net edge weight
    score += max(net_edge, 0) * 0.001
    # stability weight
    score += max(stability, 0) * 0.3
    # freshness penalty
    score -= min(freshness / 1000, 60) * 0.002

    return max(0.0, min(1.0, score))


def to_recommendation(
    opportunity: OpportunityRecord,
    signals: OpportunitySignals,
    rank: int,
) -> RankedRecommendation:
    quality_score = score_signals(signals.values)
    reasons = classify_reasons(signals.values, seen_count=int(signals.values.get("seen_count", 0)))
    economics = {
        "symbol": opportunity.opportunity.symbol,
        "buy_venue": opportunity.opportunity.buy.venue,
        "sell_venue": opportunity.opportunity.sell.venue,
        "gross_edge_bps": opportunity.opportunity.edge_bps,
        "net_edge_bps": opportunity.opportunity.net_edge,
        "currency": opportunity.opportunity.ccy,
    }
    return RankedRecommendation(
        opportunity_id=signals.opportunity_id,
        rank=rank,
        quality_score=quality_score,
        reasons=reasons,
        signals=signals.values,
        economics=economics,
    )


def rank_opportunities(recommendations: Iterable[RankedRecommendation]) -> List[RankedRecommendation]:
    sorted_recs = sorted(recommendations, key=lambda r: r.quality_score, reverse=True)
    for idx, rec in enumerate(sorted_recs, start=1):
        rec.rank = idx
    return sorted_recs


__all__ = ["RankedRecommendation", "score_signals", "to_recommendation", "rank_opportunities"]
