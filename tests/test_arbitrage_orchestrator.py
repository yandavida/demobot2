from datetime import datetime

import pytest

from core.arbitrage.feed import QuoteSnapshot
from core.arbitrage.models import ArbitrageConfig, VenueQuote
from core.arbitrage.orchestrator import ArbitrageOrchestrator
from core.fx.converter import FxConverter
from core.fx.provider import FxRateProvider
from core.portfolio.models import Currency
from core.services.arbitrage_orchestration import (
    create_arbitrage_session,
    get_session_history,
    ingest_quotes_and_scan,
)


@pytest.mark.parametrize("base_currency", ["ILS", "USD"])
def test_create_session_and_ingest(base_currency: Currency) -> None:
    orchestrator = ArbitrageOrchestrator()
    config = ArbitrageConfig(min_edge_bps=0.0, default_size=1.0)
    state = orchestrator.create_session(base_currency=base_currency, config=config)

    assert state.session_id in orchestrator.sessions
    assert state.config.min_edge_bps == 0.0

    quotes = [
        VenueQuote(venue="Alpha", symbol="XYZ", ccy="USD", bid=101.0, ask=100.0, size=5),
        VenueQuote(venue="Bravo", symbol="XYZ", ccy="USD", bid=102.0, ask=101.0, size=2),
    ]
    snapshot = QuoteSnapshot(as_of=datetime.utcnow(), quotes=quotes)
    fx_converter = FxConverter(
        provider=FxRateProvider.from_usd_ils(3.5), base_ccy=base_currency
    )

    records = orchestrator.ingest_snapshot(
        session_id=state.session_id, snapshot=snapshot, fx_converter=fx_converter
    )

    assert len(records) == 1
    record = records[0]
    assert record.opportunity.symbol == "XYZ"
    assert record.edge_total.ccy == base_currency
    assert record.edge_total.amount > 0
    assert len(state.snapshots) == 1
    assert len(state.opportunities_history) == 1


def test_services_round_trip_history() -> None:
    config = ArbitrageConfig(min_edge_bps=0.0, default_size=1.0)
    session_id = create_arbitrage_session(base_currency="ILS", config=config)

    quotes_payload = [
        {"symbol": "ES", "venue": "EX_A", "ccy": "USD", "bid": 4998.0, "ask": 4999.0},
        {"symbol": "ES", "venue": "EX_B", "ccy": "USD", "bid": 5002.0, "ask": 5002.5},
    ]

    scan_result = ingest_quotes_and_scan(
        session_id=session_id, quotes_payload=quotes_payload, fx_rate_usd_ils=3.6
    )

    assert len(scan_result) == 1
    opp = scan_result[0]
    assert opp["symbol"] == "ES"
    assert opp["currency"] == "ILS"

    history = get_session_history(session_id=session_id, symbol="ES")
    assert len(history) == 1
    assert history[0]["gross_edge_total"] == opp["gross_edge_total"]
