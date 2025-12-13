from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from core.arbitrage.feed import QuoteSnapshot
from core.arbitrage.intelligence.lifecycle import OpportunityState
from core.arbitrage.models import ArbitrageConfig
from core.arbitrage.orchestrator import ArbitrageOrchestrator
from core.arbitrage.quote_validation import MAX_VALIDATION_ISSUES, validate_quotes
from core.fx.converter import FxConverter
from core.fx.provider import FxRateProvider
from core.portfolio.models import Currency

_orchestrator = ArbitrageOrchestrator()


class StrictValidationError(Exception):
    def __init__(self, summary: dict[str, object]):
        super().__init__("Strict validation failed")
        self.summary = summary


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


def _with_validation_summary(
    payload: dict[str, Any], summary: dict[str, object] | None
) -> dict[str, Any]:
    payload["validation_summary"] = summary
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
    fx_rate_usd_ils: float = 3.5,
    strict_validation: bool = False,
) -> Dict[str, Any]:
    session = _orchestrator.get_session(session_id)
    valid_quotes, validation_summary = validate_quotes(
        quotes_payload,
        max_issues=MAX_VALIDATION_ISSUES,
        default_ccy=str(session.base_currency),
    )
    summary_payload = validation_summary.to_dict()
    session.validation_summary = summary_payload

    if strict_validation and validation_summary.total_issues:
        raise StrictValidationError(summary_payload)

    snapshot = QuoteSnapshot(as_of=datetime.utcnow(), quotes=list(valid_quotes))

    fx_provider = FxRateProvider.from_usd_ils(fx_rate_usd_ils)
    fx_converter = FxConverter(provider=fx_provider, base_ccy=session.base_currency)

    opportunities = _orchestrator.ingest_snapshot(
        session_id=session_id, snapshot=snapshot, fx_converter=fx_converter
    )
    payload = [
        _attach_execution_readiness(
            opp.to_summary(),
            session.opportunity_state.get(opp.opportunity.opportunity_id),
            readiness=opp.execution_readiness,
            decision=opp.execution_decision,
        )
        for opp in opportunities
    ]

    return _with_validation_summary(
        {"opportunities": payload}, summary=session.validation_summary
    )


def get_session_history(
    session_id: UUID, symbol: str | None = None
) -> Dict[str, Any]:
    session = _orchestrator.get_session(session_id)
    records = _orchestrator.get_opportunity_time_series(
        session_id=session_id, symbol=symbol
    )
    payload = [
        _attach_execution_readiness(
            record.to_summary(),
            session.opportunity_state.get(record.opportunity.opportunity_id),
            readiness=record.execution_readiness,
            decision=record.execution_decision,
        )
        for record in records
    ]
    return _with_validation_summary({"opportunities": payload}, session.validation_summary)


def get_top_recommendations(
    session_id: UUID, limit: int = 10, symbol: str | None = None
) -> Dict[str, Any]:
    session = _orchestrator.get_session(session_id)
    recs = _orchestrator.get_recommendations(
        session_id=session_id, limit=limit, symbol=symbol
    )

    result: list[Dict[str, Any]] = []
    for rec in recs:
        embedded = getattr(rec, "execution_readiness", None)
        lifecycle = session.opportunity_state.get(rec.opportunity_id)
        execution_readiness = _serialize_execution_readiness(
            lifecycle, readiness=embedded, decision=getattr(rec, "execution_decision", None)
        )

        result.append(
            {
                "opportunity_id": rec.opportunity_id,
                "rank": rec.rank,
                "quality_score": rec.quality_score,
                "reasons": [{"code": r.code, "detail": r.detail} for r in rec.reasons],
                "signals": rec.signals,
                "economics": rec.economics,
                "execution_readiness": execution_readiness,
                "execution_decision": execution_readiness.get("decision")
                if execution_readiness
                else None,
            }
        )
    return _with_validation_summary({"recommendations": result}, session.validation_summary)


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
        "validation_summary": state.validation_summary,
    }


def get_history_window(
    session_id: UUID, symbol: str | None = None, limit: int = 200
) -> Dict[str, Any]:
    state = _orchestrator.get_session(session_id)
    history = state.opportunities_history
    filtered = [h for h in history if symbol is None or h.opportunity.symbol == symbol]
    payload = [
        _attach_execution_readiness(
            h.to_summary(),
            state.opportunity_state.get(h.opportunity.opportunity_id),
            readiness=h.execution_readiness,
            decision=h.execution_decision,
        )
        for h in filtered[-limit:]
    ]
    return _with_validation_summary({"opportunities": payload}, state.validation_summary)


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
            {
                "opportunity_id": opp_id,
                "symbol": opp_symbol,
                **(readiness_payload or {}),
            }
        )

    return readiness
