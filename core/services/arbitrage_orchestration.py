from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from pydantic import BaseModel, field_validator

from core.arbitrage.feed import QuoteSnapshot
from core.arbitrage.intelligence.lifecycle import OpportunityState
from core.arbitrage.models import ArbitrageConfig, VenueQuote
from core.arbitrage.orchestrator import ArbitrageOrchestrator
from core.fx.converter import FxConverter
from core.fx.provider import FxRateProvider
from core.market_data import validate_quotes_payload
from core.portfolio.models import Currency

_orchestrator = ArbitrageOrchestrator()


class QuotePayload(BaseModel):
    """Strict schema for validating incoming quote payloads.

    Notes:
    - strict_validation=True will use this schema and fail-fast via ValidationError.
    - Keep fields aligned with VenueQuote + any tolerated metadata (e.g. latency_ms).
    """

    symbol: str
    venue: str
    ccy: str = "USD"
    bid: float
    ask: float
    size: float | None = None
    fees_bps: float | None = 0.0
    latency_ms: float | None = None

    @field_validator("bid", "ask")
    @classmethod
    def _require_positive(cls, value: float) -> float:
        if value is None:
            raise ValueError("Quote must include bid/ask")
        if value <= 0:
            raise ValueError("Bid/ask must be positive")
        return value


def _normalize_execution_readiness(readiness: Any | None) -> dict[str, object] | None:
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


def _summarize_validations(results: list[Any]) -> dict[str, object]:
    valid = sum(1 for r in results if getattr(r, "is_valid", False))
    invalid = len(results) - valid

    def _collect(kind: str) -> list[dict[str, object]]:
        collected: list[dict[str, object]] = []
        for idx, result in enumerate(results):
            messages = getattr(result, kind, None)
            if messages:
                collected.append({"index": idx, "messages": list(messages)})
        return collected

    return {
        "total": len(results),
        "valid": valid,
        "invalid": invalid,
        "errors": _collect("errors"),
        "warnings": _collect("warnings"),
    }


def create_arbitrage_session(
    base_currency: Currency,
    config: ArbitrageConfig,
) -> UUID:
    state = _orchestrator.create_session(base_currency=base_currency, config=config)
    return state.session_id


def _validate_quotes_payload_strict(
    quotes_payload: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Strict validation + normalization.

    Raises:
        ValidationError: if any quote fails the strict schema.
    """
    validated = [QuotePayload.model_validate(quote) for quote in quotes_payload]
    return [quote.model_dump() for quote in validated]


def ingest_quotes_and_scan(
    session_id: UUID,
    quotes_payload: List[Dict[str, Any]],
    fx_rate_usd_ils: float,
    strict_validation: bool = False,
) -> Dict[str, Any]:
    session = _orchestrator.get_session(session_id)

    quote_validation: dict[str, object] | None = None
    normalized_payload: List[Dict[str, Any]] = quotes_payload

    if strict_validation:
        # Fail-fast, let API layer convert ValidationError to HTTP 422.
        normalized_payload = _validate_quotes_payload_strict(quotes_payload)
        quote_validation = None
    else:
        validation_results = validate_quotes_payload(quotes_payload)
        quote_validation = _summarize_validations(validation_results)

        normalized_payload = []
        for payload, result in zip(quotes_payload, validation_results):
            if not getattr(result, "is_valid", False):
                continue
            source = getattr(result, "normalized", None) or payload
            normalized_payload.append(source)

    quotes: List[VenueQuote] = [
        VenueQuote(
            venue=q.get("venue"),
            symbol=q.get("symbol"),
            ccy=q.get("ccy", session.base_currency),
            bid=q.get("bid"),
            ask=q.get("ask"),
            size=q.get("size"),
            fees_bps=q.get("fees_bps", 0.0),
            latency_ms=q.get("latency_ms"),
        )
        for q in normalized_payload
    ]

    snapshot = QuoteSnapshot(as_of=datetime.utcnow(), quotes=quotes)

    fx_provider = FxRateProvider.from_usd_ils(fx_rate_usd_ils)
    fx_converter = FxConverter(provider=fx_provider, base_ccy=session.base_currency)

    opportunities = _orchestrator.ingest_snapshot(
        session_id=session_id, snapshot=snapshot, fx_converter=fx_converter
    )

    opp_payload = [
        _attach_execution_readiness(
            opp.to_summary(),
            session.opportunity_state.get(opp.opportunity.opportunity_id),
            readiness=opp.execution_readiness,
            decision=opp.execution_decision,
        )
        for opp in opportunities
    ]

    # Keep legacy key name for compatibility with earlier branch output.
    return {
        "opportunities": opp_payload,
        "quote_validation": quote_validation,
        "validation_summary": quote_validation,
    }


def get_session_history(
    session_id: UUID, symbol: str | None = None
) -> List[Dict[str, Any]]:
    session = _orchestrator.get_session(session_id)
    records = _orchestrator.get_opportunity_time_series(session_id=session_id, symbol=symbol)
    return [
        _attach_execution_readiness(
            record.to_summary(),
            session.opportunity_state.get(record.opportunity.opportunity_id),
            readiness=record.execution_readiness,
            decision=record.execution_decision,
        )
        for record in records
    ]


def get_top_recommendations(
    session_id: UUID, limit: int = 10, symbol: str | None = None
) -> List[Dict[str, Any]]:
    session = _orchestrator.get_session(session_id)
    recs = _orchestrator.get_recommendations(session_id=session_id, limit=limit, symbol=symbol)

    result: list[Dict[str, Any]] = []
    for rec in recs:
        embedded = getattr(rec, "execution_readiness", None)
        lifecycle = session.opportunity_state.get(rec.opportunity_id)
        execution_readiness = _serialize_execution_readiness(
            lifecycle,
            readiness=embedded,
            decision=getattr(rec, "execution_decision", None),
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
                "execution_decision": execution_readiness.get("decision") if execution_readiness else None,
            }
        )
    return result


def get_opportunity_detail(
    session_id: UUID, opportunity_id: str
) -> Dict[str, Any] | None:
    state = _orchestrator.get_session(session_id)
    history = [r for r in state.opportunities_history if r.opportunity.opportunity_id == opportunity_id]
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
    }


def get_history_window(
    session_id: UUID, symbol: str | None = None, limit: int = 200
) -> List[Dict[str, Any]]:
    state = _orchestrator.get_session(session_id)
    history = state.opportunities_history
    filtered = [h for h in history if symbol is None or h.opportunity.symbol == symbol]
    return [
        _attach_execution_readiness(
            h.to_summary(),
            state.opportunity_state.get(h.opportunity.opportunity_id),
            readiness=h.execution_readiness,
            decision=h.execution_decision,
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

    symbol_by_opportunity: dict[str, str] = {}
    for record in state.opportunities_history:
        symbol_by_opportunity[record.opportunity.opportunity_id] = record.opportunity.symbol

    readiness_by_opportunity: dict[str, Any | None] = {}
    decision_by_opportunity: dict[str, Any | None] = {}
    for record in state.opportunities_history:
        readiness_by_opportunity[record.opportunity.opportunity_id] = record.execution_readiness
        decision_by_opportunity[record.opportunity.opportunity_id] = record.execution_decision

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
