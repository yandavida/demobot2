from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
from uuid import UUID, uuid4

from core.arbitrage.engine import find_cross_venue_opportunities
from core.arbitrage.feed import QuoteSnapshot
from core.arbitrage.models import ArbitrageConfig, ArbitrageOpportunity
from core.fx.converter import FxConverter
from core.portfolio.models import Currency, Money


@dataclass
class OpportunityRecord:
    """Enriched opportunity with monetary values converted to base currency."""

    as_of: datetime
    opportunity: ArbitrageOpportunity
    edge_per_unit: Money
    edge_total: Money

    def to_summary(self) -> dict[str, object]:
        return {
            "timestamp": self.as_of.isoformat(),
            "symbol": self.opportunity.symbol,
            "buy_venue": self.opportunity.buy.venue,
            "sell_venue": self.opportunity.sell.venue,
            "quantity": self.opportunity.size,
            "edge_bps": self.opportunity.edge_bps,
            "gross_edge_per_unit": self.edge_per_unit.amount,
            "gross_edge_total": self.edge_total.amount,
            "currency": self.edge_total.ccy,
        }


@dataclass
class ArbitrageSessionState:
    session_id: UUID
    base_currency: Currency
    config: ArbitrageConfig
    snapshots: List[QuoteSnapshot] = field(default_factory=list)
    opportunities_history: List[OpportunityRecord] = field(default_factory=list)


@dataclass
class ArbitrageOrchestrator:
    """In-memory arbitrage orchestrator managing multiple sessions."""

    sessions: Dict[UUID, ArbitrageSessionState] = field(default_factory=dict)

    def create_session(
        self,
        base_currency: Currency,
        config: ArbitrageConfig,
    ) -> ArbitrageSessionState:
        session_id = uuid4()
        state = ArbitrageSessionState(
            session_id=session_id,
            base_currency=base_currency,
            config=config,
        )
        self.sessions[session_id] = state
        return state

    def list_sessions(self) -> List[ArbitrageSessionState]:
        return list(self.sessions.values())

    def get_session(self, session_id: UUID) -> ArbitrageSessionState:
        return self.sessions[session_id]

    def ingest_snapshot(
        self,
        session_id: UUID,
        snapshot: QuoteSnapshot,
        fx_converter: FxConverter,
    ) -> List[OpportunityRecord]:
        state = self.get_session(session_id)
        state.snapshots.append(snapshot)

        opportunities = find_cross_venue_opportunities(
            quotes=snapshot.quotes,
            config=state.config,
        )

        enriched: list[OpportunityRecord] = []
        for opp in opportunities:
            edge_per_unit_money = fx_converter.to_base(
                Money(amount=opp.net_edge, ccy=opp.ccy)
            )
            edge_total_money = fx_converter.to_base(
                Money(amount=opp.net_edge * opp.size, ccy=opp.ccy)
            )
            record = OpportunityRecord(
                as_of=snapshot.as_of,
                opportunity=opp,
                edge_per_unit=edge_per_unit_money,
                edge_total=edge_total_money,
            )
            state.opportunities_history.append(record)
            enriched.append(record)

        return enriched

    def get_latest_opportunities(self, session_id: UUID, limit: int = 50) -> List[OpportunityRecord]:
        state = self.get_session(session_id)
        return state.opportunities_history[-limit:]

    def get_opportunity_time_series(
        self,
        session_id: UUID,
        symbol: str | None = None,
    ) -> List[OpportunityRecord]:
        state = self.get_session(session_id)
        if symbol is None:
            return list(state.opportunities_history)
        return [opp for opp in state.opportunities_history if opp.opportunity.symbol == symbol]
