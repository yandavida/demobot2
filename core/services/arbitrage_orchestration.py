from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from core.arbitrage.feed import QuoteSnapshot
from core.arbitrage.intelligence.lifecycle import OpportunityState
from core.arbitrage.models import ArbitrageConfig, VenueQuote
from core.arbitrage.orchestrator import ArbitrageOrchestrator, ValidationSummary
from core.fx.converter import FxConverter
from core.fx.provider import FxRateProvider
from core.portfolio.models import Currency

_orchestrator = ArbitrageOrchestrator()


def _normalize_execution_readiness(
    readiness: Any | None,
) -> dict[str, object] | None:
    if readiness is None:
        return None

    if hasattr(readiness, "to_dict"):
        return readiness.to_dict()

    if isinstance(readiness, dict):
        return readiness

    return None


def _serialize_execution_decision(decision: Any | None) -> dict[str, object] | None:
    if decision is None:
        return None

    if hasattr(decision, "reason"):
        return {
            "reason": getattr(decision.reason, "value", decision.reason),
            "can_execute": getattr(decision, "should_execute", False),
            "reason_codes": [getattr(decision.reason, "value", decision.reason)],
            "metrics": {
                "edge_bps": getattr(decision, "edge_bps", None),
                "spread_bps": getattr(decision, "worst_spread_bps", None),
                "age_ms": getattr(decision, "age_ms", None),
                "notional": getattr(decision, "notional", None),
                "qty": getattr(decision, "recommended_qty", None),
            },
            "recommended_qty": getattr(decision, "recommended_qty", None),
        }

    if isinstance(decision, dict):
        return decision

    return None


def _serialize_validation_summary(summary: ValidationSummary | dict[str, Any] | None) -> dict[str, Any] | None:
    if summary is None:
        return None

    if isinstance(summary, dict):
        return summary

    if hasattr(summary, "to_dict"):
        return summary.to_dict()  # type: ignore[no-any-return]

    return None


def _serialize_execution_readiness(
    lifecycle: OpportunityState | None,
    readiness: Any | None = None,
    decision: Any | None = None,
) -> dict[str, object] | None:
    lifecycle_payload: dict[str, object] | None = None
    if lifecycle is not None:
        lifecycle_payload = {
            "state": lifecycle.state.value,
            "first_seen": lifecycle.first_seen.isoformat(),
            "last_seen": lifecycle.last_seen.isoformat(),
            "seen_count": lifecycle.seen_count,
            "last_edge_bps": lifecycle.last_edge_bps,
            "last_net_edge_bps": lifecycle.last_net_edge_bps,
        }

    readiness_payload = _normalize_execution_readiness(readiness)
    decision_payload = _serialize_execution_decision(decision)

    if lifecycle_payload is None and readiness_payload is None and decision_payload is None:
        return None

    payload: dict[str, object] = {}
    if decision_payload:
        payload["decision"] = decision_payload
        payload.setdefault("can_execute", decision_payload.get("can_execute"))
        payload.setdefault("reason_codes", decision_payload.get("reason_codes"))
        if "metrics" in decision_payload:
            payload.setdefault("metrics", decision_payload["metrics"])
        if "recommended_qty" in decision_payload:
            payload.setdefault("recommended_qty", decision_payload["recommended_qty"])
    if readiness_payload:
        payload.update(readiness_payload)
    if lifecycle_payload:
        payload.update(lifecycle_payload)
    return payload


def _attach_execution_readiness(
    summary: dict[str, Any],
    lifecycle: OpportunityState | None,
    readiness: Any | None = None,
    decision: Any | None = None,
) -> dict[str, Any]:
    readiness_payload = _serialize_execution_readiness(
        lifecycle, readiness=readiness, decision=decision
    )
    decision_payload = readiness_payload.get("decision") if readiness_payload else None
    if readiness_payload is not None:
        summary["execution_readiness"] = readiness_payload
    if decision_payload is None:
        decision_payload = _serialize_execution_decision(decision)
    if decision_payload is not None:
        summary["execution_decision"] = decision_payload
    return summary


def _attach_validation_summary(
    payload: dict[str, Any], summary: ValidationSummary | dict[str, Any] | None
) -> dict[str, Any]:
    payload["validation_summary"] = _serialize_validation_summary(summary)
    return payload


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
    validation_summary = _serialize_validation_summary(session.last_validation_summary)
    return [
        _attach_validation_summary(
            _attach_execution_readiness(
                opp.to_summary(),
                session.opportunity_state.get(opp.opportunity.opportunity_id),
                readiness=opp.execution_readiness,
                decision=opp.execution_decision,
            ),
            validation_summary,
        )
        for opp in opportunities
    ]


def get_session_history(
    session_id: UUID, symbol: str | None = None
) -> List[Dict[str, Any]]:
    session = _orchestrator.get_session(session_id)
    records = _orchestrator.get_opportunity_time_series(
        session_id=session_id, symbol=symbol
    )
    validation_summary = _serialize_validation_summary(session.last_validation_summary)
    return [
        _attach_validation_summary(
            _attach_execution_readiness(
                record.to_summary(),
                session.opportunity_state.get(record.opportunity.opportunity_id),
                readiness=record.execution_readiness,
                decision=record.execution_decision,
            ),
            validation_summary,
        )
        for record in records
    ]


def get_top_recommendations(
    session_id: UUID, limit: int = 10, symbol: str | None = None
) -> List[Dict[str, Any]]:
    session = _orchestrator.get_session(session_id)
    recs = _orchestrator.get_recommendations(
        session_id=session_id, limit=limit, symbol=symbol
    )

    result: list[Dict[str, Any]] = []
    validation_summary = _serialize_validation_summary(session.last_validation_summary)
    for rec in recs:
        embedded = getattr(rec, "execution_readiness", None)
        lifecycle = session.opportunity_state.get(rec.opportunity_id)
        execution_readiness = _serialize_execution_readiness(
            lifecycle, readiness=embedded, decision=getattr(rec, "execution_decision", None)
        )

        result.append(
            _attach_validation_summary(
                {
                    "opportunity_id": rec.opportunity_id,
                    "rank": rec.rank,
                    "quality_score": rec.quality_score,
                    "reasons": [
                        {"code": r.code, "detail": r.detail} for r in rec.reasons
                    ],
                    "signals": rec.signals,
                    "economics": rec.economics,
                    "execution_readiness": execution_readiness,
                    "execution_decision": execution_readiness.get("decision")
                    if execution_readiness
                    else None,
                },
                validation_summary,
            )
        )
    return result


def get_opportunity_detail(
    session_id: UUID, opportunity_id: str
) -> Dict[str, Any] | None:
    state = _orchestrator.get_session(session_id)
    history = [
        r
        for r in state.opportunities_history
        if r.opportunity.opportunity_id == opportunity_id
    ]
    if not history:
        return None

    latest = history[-1]
    opp_state = state.opportunity_state.get(opportunity_id)
    validation_summary = _serialize_validation_summary(state.last_validation_summary)

    signals: dict[str, float] = {}
    reasons: list[Any] = []

    if opp_state:
        recs = _orchestrator.get_recommendations(
            session_id=session_id,
            limit=len(state.opportunities_history),
            symbol=None,
        )
        for rec in recs:
            if rec.opportunity_id == opportunity_id:
                signals = rec.signals or {}
                reasons = rec.reasons or []
                break

    return {
        "opportunity": latest.to_summary(),
        "state": opp_state.state if opp_state else None,
        "signals": signals,
        "reasons": [{"code": r.code, "detail": r.detail} for r in reasons],
        "execution_readiness": _serialize_execution_readiness(
            opp_state,
            readiness=latest.execution_readiness,
            decision=latest.execution_decision,
        ),
        "execution_decision": _serialize_execution_decision(latest.execution_decision),
        "validation_summary": validation_summary,
    }


def get_history_window(
    session_id: UUID, symbol: str | None = None, limit: int = 200
) -> List[Dict[str, Any]]:
    state = _orchestrator.get_session(session_id)
    history = state.opportunities_history
    filtered = [h for h in history if symbol is None or h.opportunity.symbol == symbol]
    validation_summary = _serialize_validation_summary(state.last_validation_summary)
    return [
        _attach_validation_summary(
            _attach_execution_readiness(
                h.to_summary(),
                state.opportunity_state.get(h.opportunity.opportunity_id),
                readiness=h.execution_readiness,
                decision=h.execution_decision,
            ),
            validation_summary,
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


def get_readiness_states(
    session_id: UUID, symbol: str | None = None
) -> List[Dict[str, Any]]:
    state = _orchestrator.get_session(session_id)
    validation_summary = _serialize_validation_summary(state.last_validation_summary)

    symbol_by_opportunity: dict[str, str] = {}
    for record in state.opportunities_history:
        symbol_by_opportunity[record.opportunity.opportunity_id] = record.opportunity.symbol

    readiness_by_opportunity: dict[str, Any | None] = {}
    decision_by_opportunity: dict[str, Any | None] = {}
    for record in state.opportunities_history:
        readiness_by_opportunity[record.opportunity.opportunity_id] = (
            record.execution_readiness
        )
        decision_by_opportunity[record.opportunity.opportunity_id] = (
            record.execution_decision
        )

    readiness: list[Dict[str, Any]] = []
    for opp_id, lifecycle in state.opportunity_state.items():
        opp_symbol = symbol_by_opportunity.get(opp_id)
        if symbol and opp_symbol != symbol:
            continue

        readiness_payload = _serialize_execution_readiness(
            lifecycle,
            readiness=readiness_by_opportunity.get(opp_id),
            decision=decision_by_opportunity.get(opp_id),
        )
        readiness.append(
            _attach_validation_summary(
                {
                    "opportunity_id": opp_id,
                    "symbol": opp_symbol,
                    **(readiness_payload or {}),
                },
                validation_summary,
            )
        )

    return readiness
