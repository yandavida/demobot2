from datetime import datetime, timedelta

import pytest

from core.arbitrage.intelligence.lifecycle import LifecycleState
from core.arbitrage.intelligence.limits import SessionLimits
from core.arbitrage.orchestrator import ArbitrageOrchestrator
from core.arbitrage.models import ArbitrageConfig, VenueQuote
from core.arbitrage.feed import QuoteSnapshot
from core.fx.converter import FxConverter
from core.fx.provider import FxRateProvider


@pytest.fixture()
def orchestrator() -> ArbitrageOrchestrator:
    return ArbitrageOrchestrator(limits=SessionLimits(ttl_seconds=1, max_snapshots=2, max_events=3))


def test_lifecycle_transitions(orchestrator: ArbitrageOrchestrator) -> None:
    config = ArbitrageConfig(min_edge_bps=0.0, default_size=1.0)
    state = orchestrator.create_session(base_currency="USD", config=config)

    now = datetime.utcnow()
    snapshot = QuoteSnapshot(
        as_of=now,
        quotes=[
            VenueQuote(venue="A", symbol="ES", bid=101.0, ask=100.0, ccy="USD"),
            VenueQuote(venue="B", symbol="ES", bid=102.0, ask=101.0, ccy="USD"),
        ],
    )
    fx_converter = FxConverter(provider=FxRateProvider.from_usd_ils(3.5), base_ccy="USD")
    orchestrator.ingest_snapshot(session_id=state.session_id, snapshot=snapshot, fx_converter=fx_converter)

    opp_state = list(state.opportunity_state.values())[0]
    assert opp_state.state == LifecycleState.NEW

    later = now + timedelta(seconds=0.1)
    snapshot2 = QuoteSnapshot(
        as_of=later,
        quotes=[
            VenueQuote(venue="A", symbol="ES", bid=101.001, ask=100.0, ccy="USD"),
            VenueQuote(venue="B", symbol="ES", bid=102.0, ask=101.0, ccy="USD"),
        ],
    )
    orchestrator.ingest_snapshot(session_id=state.session_id, snapshot=snapshot2, fx_converter=fx_converter)

    opp_state = list(state.opportunity_state.values())[0]
    assert opp_state.state == LifecycleState.ACTIVE

    expired_time = now + timedelta(seconds=2)
    orchestrator.ingest_snapshot(
        session_id=state.session_id,
        snapshot=QuoteSnapshot(as_of=expired_time, quotes=snapshot2.quotes),
        fx_converter=fx_converter,
    )
    # expired state should be recreated as NEW after TTL
    opp_state = list(state.opportunity_state.values())[0]
    assert opp_state.state == LifecycleState.NEW
    assert opp_state.seen_count == 1


def test_window_pruning(orchestrator: ArbitrageOrchestrator) -> None:
    config = ArbitrageConfig(min_edge_bps=0.0, default_size=1.0)
    state = orchestrator.create_session(base_currency="USD", config=config)
    fx_converter = FxConverter(provider=FxRateProvider.from_usd_ils(3.5), base_ccy="USD")
    now = datetime.utcnow()
    for i in range(5):
        snapshot = QuoteSnapshot(
            as_of=now + timedelta(seconds=i),
            quotes=[
                VenueQuote(venue="A", symbol=f"ES{i}", bid=101 + i, ask=100 + i, ccy="USD"),
                VenueQuote(venue="B", symbol=f"ES{i}", bid=102 + i, ask=101 + i, ccy="USD"),
            ],
        )
        orchestrator.ingest_snapshot(session_id=state.session_id, snapshot=snapshot, fx_converter=fx_converter)

    assert len(state.snapshots) <= orchestrator.limits.max_snapshots
    assert len(state.events) <= orchestrator.limits.max_events
    assert len(state.opportunities_history) <= orchestrator.limits.max_snapshots
