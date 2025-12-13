from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from core.arbitrage.intelligence.lifecycle import OpportunityState
from core.arbitrage.feed import QuoteSnapshot
from core.arbitrage.models import ArbitrageConfig, VenueQuote
from core.arbitrage.orchestrator import ArbitrageOrchestrator
from core.fx.converter import FxConverter
from core.fx.provider import FxRateProvider
from core.portfolio.models import Currency

_orchestrator = ArbitrageOrchestrator()


def _serialize_execution_readiness(
    state: OpportunityState | None,
) -> dict[str, object] | None:
    if state is None:
        return None
    return {
        "state": state.state.value,
        "first_seen": state.first_seen.isoformat(),
        "last_seen": state.last_seen.isoformat(),
        "seen_count": state.seen_count,
        "last_edge_bps": state.last_edge_bps,
        "last_net_edge_bps": state.last_net_edge_bps,
    }


def _attach_execution_readiness(
    summary: dict[str, Any], state: OpportunityState | None
) -> dict[str, Any]:
    readiness = _serialize_execution_readiness(state)
    if readiness is not None:
        summary["execution_readiness"] = readiness
    return summary


def create_arbitrage_session(
    base_currency: Currency,
    config: ArbitrageConfig,
) -> UUID:
    state = _orchestrator.create_session(base_currency=base_currency, config=config)
    return state.session_id


def ingest_quotes_and_scan(
    session_id: UUID,
    quotes_payload: List[Dict[str, Any]],
    fx_rate_usd_ils: float,
) -> List[Dict[str, Any]]:
    session = _orchestrator.get_session(session_id)
    quotes: List[VenueQuote] = [
        VenueQuote(
            venue=q["venue"],
            symbol=q["symbol"],
            ccy=q.get("ccy", session.base_currency),
            bid=q.get("bid"),
            ask=q.get("ask"),
            size=q.get("size"),
            fees_bps=q.get("fees_bps", 0.0),
        )
        for q in quotes_payload
    ]
    snapshot = QuoteSnapshot(as_of=datetime.utcnow(), quotes=quotes)

    fx_provider = FxRateProvider.from_usd_ils(fx_rate_usd_ils)
    fx_converter = FxConverter(provider=fx_provider, base_ccy=session.base_currency)

    opportunities = _orchestrator.ingest_snapshot(
        session_id=session_id, snapshot=snapshot, fx_converter=fx_converter
    )
    return [
        _attach_execution_readiness(
            opp.to_summary(),
            session.opportunity_state.get(opp.opportunity.opportunity_id),
        )
        for opp in opportunities
    ]


def get_session_history(session_id: UUID, symbol: str | None = None) -> List[Dict[str, Any]]:
    session = _orchestrator.get_session(session_id)
    records = _orchestrator.get_opportunity_time_series(session_id=session_id, symbol=symbol)
    return [
        _attach_execution_readiness(
            record.to_summary(),
            session.opportunity_state.get(record.opportunity.opportunity_id),
        )
        for record in records
    ]


def get_top_recommendations(session_id: UUID, limit: int = 10, symbol: str | None = None) -> List[Dict[str, Any]]:
    session = _orchestrator.get_session(session_id)
    recs = _orchestrator.get_recommendations(session_id=session_id, limit=limit, symbol=symbol)
    result: list[Dict[str, Any]] = []
    for rec in recs:
        readiness = _serialize_execution_readiness(
            session.opportunity_state.get(rec.opportunity_id)
        )
        result.append(
            {
                "opportunity_id": rec.opportunity_id,
                "rank": rec.rank,
                "quality_score": rec.quality_score,
                "reasons": [
                    {"code": r.code, "detail": r.detail}
                    for r in rec.reasons
                ],
                "signals": rec.signals,
                "economics": rec.economics,
                "execution_readiness": readiness,
            }
        )
    return result


def get_opportunity_detail(session_id: UUID, opportunity_id: str) -> Dict[str, Any] | None:
    state = _orchestrator.get_session(session_id)
    history = [r for r in state.opportunities_history if r.opportunity.opportunity_id == opportunity_id]
    if not history:
        return None
    latest = history[-1]
    opp_state = state.opportunity_state.get(opportunity_id)
    signals = None
    reasons = None
    if opp_state:
        recs = _orchestrator.get_recommendations(
            session_id=session_id,
            limit=len(state.opportunities_history),
            symbol=None,
        )
        signals_map: dict[str, float] | None = None
        for rec in recs:
            if rec.opportunity_id == opportunity_id:
                signals_map = rec.signals
                reasons = rec.reasons
                break
        signals = signals_map or {}
    return {
        "opportunity": latest.to_summary(),
        "state": opp_state.state if opp_state else None,
        "signals": signals or {},
        "reasons": [
            {"code": r.code, "detail": r.detail} for r in reasons or []
        ],
        "execution_readiness": _serialize_execution_readiness(opp_state),
    }


def get_history_window(session_id: UUID, symbol: str | None = None, limit: int = 200) -> List[Dict[str, Any]]:
    state = _orchestrator.get_session(session_id)
    history = state.opportunities_history
    filtered = [h for h in history if symbol is None or h.opportunity.symbol == symbol]
    return [
        _attach_execution_readiness(
            h.to_summary(), state.opportunity_state.get(h.opportunity.opportunity_id)
        )
        for h in filtered[-limit:]
    ]


def list_sessions() -> List[Dict[str, Any]]:
    return [
        {
            "session_id": str(session.session_id),
            "base_currency": session.base_currency,
            "snapshots": len(session.snapshots),
            "opportunities": len(session.opportunities_history),
        }
        for session in _orchestrator.list_sessions()
    ]
