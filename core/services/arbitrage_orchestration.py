from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from core.arbitrage.feed import QuoteSnapshot
from core.arbitrage.models import ArbitrageConfig, VenueQuote
from core.arbitrage.orchestrator import ArbitrageOrchestrator
from core.fx.converter import FxConverter
from core.fx.provider import FxRateProvider
from core.portfolio.models import Currency

_orchestrator = ArbitrageOrchestrator()


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
    return [opp.to_summary() for opp in opportunities]


def get_session_history(session_id: UUID, symbol: str | None = None) -> List[Dict[str, Any]]:
    records = _orchestrator.get_opportunity_time_series(session_id=session_id, symbol=symbol)
    return [record.to_summary() for record in records]


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
