from __future__ import annotations

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Deque, Dict, List
from uuid import UUID, uuid4

from core.arbitrage.engine import find_cross_venue_opportunities
from core.arbitrage.execution.gate import (
    ExecutionConstraints as ExecutionGateConstraints,
    ExecutionDecision,
    evaluate_execution_readiness as evaluate_execution_decision,
)
from core.arbitrage.identity import opportunity_id
from core.arbitrage.feed import QuoteSnapshot
from core.arbitrage.intelligence.events import ArbitrageEvent, ArbitrageEventType
from core.arbitrage.intelligence.lifecycle import (
    LifecycleState,
    OpportunityState,
    expire_stale_states,
    update_lifecycle,
)
from core.arbitrage.intelligence.limits import SessionLimits
from core.arbitrage.intelligence.signals import compute_signals
from core.arbitrage.intelligence.readiness import (
    ExecutionReadiness,
    default_execution_constraints,
    evaluate_execution_readiness,
)
from core.arbitrage.intelligence.scoring import RankedRecommendation, to_recommendation
from core.arbitrage.models import ArbitrageConfig, ArbitrageOpportunity
from core.fx.converter import FxConverter
from core.portfolio.models import Currency, Money


@dataclass
class ValidationSummary:
    as_of: datetime
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "as_of": self.as_of.isoformat(),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


@dataclass
class OpportunityRecord:
    """Enriched opportunity with monetary values converted to base currency."""

    as_of: datetime
    opportunity: ArbitrageOpportunity
    edge_per_unit: Money
    edge_total: Money
    execution_readiness: ExecutionReadiness | None = None
    execution_decision: ExecutionDecision | None = None

    def to_summary(self) -> dict[str, object]:
        return {
            "timestamp": self.as_of.isoformat(),
            "opportunity_id": self.opportunity.opportunity_id,
            "symbol": self.opportunity.symbol,
            "buy_venue": self.opportunity.buy.venue,
            "sell_venue": self.opportunity.sell.venue,
            "quantity": self.opportunity.size,
            "edge_bps": self.opportunity.edge_bps,
            "gross_edge_per_unit": self.edge_per_unit.amount,
            "gross_edge_total": self.edge_total.amount,
            "currency": self.edge_total.ccy,
            "execution_readiness": self.execution_readiness.to_dict()
            if self.execution_readiness
            else None,
            "execution_decision": {
                "reason": self.execution_decision.reason.value,
                "can_execute": self.execution_decision.should_execute,
                "reason_codes": [self.execution_decision.reason.value],
                "metrics": {
                    "edge_bps": self.execution_decision.edge_bps,
                    "spread_bps": self.execution_decision.worst_spread_bps,
                    "age_ms": self.execution_decision.age_ms,
                    "notional": self.execution_decision.notional,
                    "qty": self.execution_decision.recommended_qty,
                },
                "recommended_qty": self.execution_decision.recommended_qty,
            }
            if self.execution_decision
            else None,
        }


@dataclass
class ArbitrageSessionState:
    session_id: UUID
    base_currency: Currency
    config: ArbitrageConfig
    limits: SessionLimits
    snapshots: List[QuoteSnapshot] = field(default_factory=list)
    opportunities_history: List[OpportunityRecord] = field(default_factory=list)
    opportunity_state: Dict[str, OpportunityState] = field(default_factory=dict)
    events: Deque[ArbitrageEvent] = field(default_factory=deque)
    last_validation_summary: ValidationSummary | None = None
    last_accessed: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ArbitrageOrchestrator:
    """In-memory arbitrage orchestrator managing multiple sessions."""

    sessions: Dict[UUID, ArbitrageSessionState] = field(default_factory=dict)
    limits: SessionLimits = field(default_factory=SessionLimits)

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
            limits=self.limits,
        )
        self.sessions[session_id] = state
        return state

    def list_sessions(self) -> List[ArbitrageSessionState]:
        return list(self.sessions.values())

    def get_session(self, session_id: UUID) -> ArbitrageSessionState:
        state = self.sessions[session_id]
        state.last_accessed = datetime.utcnow()
        return state

    def ingest_snapshot(
        self,
        session_id: UUID,
        snapshot: QuoteSnapshot,
        fx_converter: FxConverter,
    ) -> List[OpportunityRecord]:
        state = self.get_session(session_id)
        validation_summary = self._validate_snapshot(snapshot)
        state.last_validation_summary = validation_summary
        expire_stale_states(state.opportunity_state, now=snapshot.as_of, limits=state.limits)
        state.snapshots.append(snapshot)
        self._prune_snapshots(state)
        state.events.append(
            ArbitrageEvent(as_of=snapshot.as_of, event_type=ArbitrageEventType.SNAPSHOT_INGESTED)
        )
        self._prune_events(state)

        opportunities = find_cross_venue_opportunities(
            quotes=snapshot.quotes,
            config=state.config,
        )

        constraints = default_execution_constraints(state.config)

        enriched: list[OpportunityRecord] = []
        gate_constraints = ExecutionGateConstraints(
            min_edge_bps=state.config.min_edge_bps,
            max_quote_age_ms=state.config.max_latency_ms,
        )

        for opp in opportunities:
            opp.as_of = snapshot.as_of
            opp.opportunity_id = opportunity_id(
                symbol=opp.symbol,
                buy_venue=opp.buy.venue,
                sell_venue=opp.sell.venue,
                base_ccy=str(state.base_currency),
                buy_price_base=fx_converter.to_base(Money(amount=opp.buy.price, ccy=opp.buy.ccy)).amount,
                sell_price_base=fx_converter.to_base(Money(amount=opp.sell.price, ccy=opp.sell.ccy)).amount,
            )
            lifecycle = update_lifecycle(
                existing=state.opportunity_state.get(opp.opportunity_id),
                as_of=snapshot.as_of,
                edge_bps=opp.edge_bps,
                net_edge_bps=opp.net_edge,
            )
            lifecycle.opportunity_id = opp.opportunity_id  # type: ignore
            state.opportunity_state[opp.opportunity_id] = lifecycle

            edge_per_unit_money = fx_converter.to_base(
                Money(amount=opp.net_edge, ccy=opp.ccy)
            )
            edge_total_money = fx_converter.to_base(
                Money(amount=opp.net_edge * opp.size, ccy=opp.ccy)
            )
            readiness = evaluate_execution_readiness(
                edge_bps=opp.edge_bps, size=opp.size, constraints=constraints
            )
            decision = evaluate_execution_decision(
                opportunity=opp,
                quotes=snapshot.quotes,
                constraints=gate_constraints,
                now=snapshot.as_of,
            )
            record = OpportunityRecord(
                as_of=snapshot.as_of,
                opportunity=opp,
                edge_per_unit=edge_per_unit_money,
                edge_total=edge_total_money,
                execution_readiness=readiness,
                execution_decision=decision,
            )
            state.opportunities_history.append(record)
            enriched.append(record)
            self._prune_history(state)
            state.events.append(
                ArbitrageEvent(
                    as_of=snapshot.as_of,
                    event_type=ArbitrageEventType.OPPORTUNITY_UPSERTED,
                    payload={"opportunity_id": opp.opportunity_id},
                )
            )

        self._prune_events(state)
        self._prune_snapshots(state)
        expire_stale_states(state.opportunity_state, now=snapshot.as_of, limits=state.limits)
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

    def get_recommendations(self, session_id: UUID, limit: int = 10, symbol: str | None = None) -> List[RankedRecommendation]:
        state = self.get_session(session_id)
        now = datetime.utcnow()
        expire_stale_states(state.opportunity_state, now=now, limits=state.limits)
        history = state.opportunities_history
        recs: list[RankedRecommendation] = []
        constraints = default_execution_constraints(state.config)
        for record in reversed(history):
            if symbol and record.opportunity.symbol != symbol:
                continue
            opp_state = state.opportunity_state.get(record.opportunity.opportunity_id)
            if not opp_state or opp_state.state == LifecycleState.EXPIRED:
                continue
            signals = compute_signals(opportunity=record, state=opp_state, now=now, history=history)
            readiness = evaluate_execution_readiness(
                edge_bps=record.opportunity.edge_bps,
                size=record.opportunity.size,
                constraints=constraints,
            )
            recommendation = to_recommendation(record, signals, rank=0)
            recommendation.execution_readiness = readiness
            recommendation.execution_decision = record.execution_decision
            recs.append(recommendation)
            if len(recs) >= limit:
                break
        ranked = sorted(recs, key=lambda r: r.quality_score, reverse=True)
        for idx, rec in enumerate(ranked, start=1):
            rec.rank = idx
        return ranked

    def prune_idle_sessions(self) -> None:
        now = datetime.utcnow()
        to_delete: list[UUID] = []
        for session_id, state in self.sessions.items():
            idle_seconds = (now - state.last_accessed).total_seconds()
            if idle_seconds >= self.limits.session_idle_expiry_seconds:
                to_delete.append(session_id)
        for session_id in to_delete:
            del self.sessions[session_id]

    def _validate_snapshot(self, snapshot: QuoteSnapshot) -> ValidationSummary:
        warnings: list[str] = []
        errors: list[str] = []

        for quote in snapshot.quotes:
            if quote.bid is None or quote.ask is None:
                warnings.append(f"Missing bid/ask for {quote.symbol} on {quote.venue}")
            if quote.bid is not None and quote.ask is not None and quote.bid <= 0:
                errors.append(f"Non-positive bid for {quote.symbol} on {quote.venue}")
            if quote.bid is not None and quote.ask is not None and quote.ask <= 0:
                errors.append(f"Non-positive ask for {quote.symbol} on {quote.venue}")

        return ValidationSummary(as_of=snapshot.as_of, warnings=warnings, errors=errors)

    def _prune_snapshots(self, state: ArbitrageSessionState) -> None:
        ttl = timedelta(seconds=state.limits.ttl_seconds)
        now = datetime.utcnow()
        state.snapshots = [s for s in state.snapshots if now - s.as_of <= ttl]
        if len(state.snapshots) > state.limits.max_snapshots:
            state.snapshots = state.snapshots[-state.limits.max_snapshots :]

    def _prune_history(self, state: ArbitrageSessionState) -> None:
        ttl = timedelta(seconds=state.limits.ttl_seconds)
        now = datetime.utcnow()
        state.opportunities_history = [
            h for h in state.opportunities_history if now - h.as_of <= ttl
        ]
        if len(state.opportunities_history) > state.limits.max_snapshots:
            state.opportunities_history = state.opportunities_history[-state.limits.max_snapshots :]

    def _prune_events(self, state: ArbitrageSessionState) -> None:
        while len(state.events) > state.limits.max_events:
            state.events.popleft()
