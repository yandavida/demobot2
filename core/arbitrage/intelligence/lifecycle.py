from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from core.arbitrage.intelligence.limits import SessionLimits


class LifecycleState(str, Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    DECAYING = "DECAYING"
    EXPIRED = "EXPIRED"


@dataclass
class OpportunityState:
    opportunity_id: str
    first_seen: datetime
    last_seen: datetime
    seen_count: int
    last_edge_bps: float
    last_net_edge_bps: float
    state: LifecycleState

    def touch(self, as_of: datetime, edge_bps: float, net_edge_bps: float) -> "OpportunityState":
        seen_count = self.seen_count + 1
        state = LifecycleState.ACTIVE if seen_count > 1 else LifecycleState.NEW
        return OpportunityState(
            opportunity_id=self.opportunity_id,
            first_seen=self.first_seen,
            last_seen=as_of,
            seen_count=seen_count,
            last_edge_bps=edge_bps,
            last_net_edge_bps=net_edge_bps,
            state=state,
        )

    def decay(self, as_of: datetime, ttl_seconds: int) -> "OpportunityState":
        idle = as_of - self.last_seen
        if idle.total_seconds() >= ttl_seconds:
            return OpportunityState(
                opportunity_id=self.opportunity_id,
                first_seen=self.first_seen,
                last_seen=self.last_seen,
                seen_count=self.seen_count,
                last_edge_bps=self.last_edge_bps,
                last_net_edge_bps=self.last_net_edge_bps,
                state=LifecycleState.EXPIRED,
            )
        return OpportunityState(
            opportunity_id=self.opportunity_id,
            first_seen=self.first_seen,
            last_seen=self.last_seen,
            seen_count=self.seen_count,
            last_edge_bps=self.last_edge_bps,
            last_net_edge_bps=self.last_net_edge_bps,
            state=LifecycleState.DECAYING,
        )


def update_lifecycle(
    existing: OpportunityState | None,
    as_of: datetime,
    edge_bps: float,
    net_edge_bps: float,
) -> OpportunityState:
    if existing is None:
        return OpportunityState(
            opportunity_id="",  # placeholder overridden by orchestrator before storing
            first_seen=as_of,
            last_seen=as_of,
            seen_count=1,
            last_edge_bps=edge_bps,
            last_net_edge_bps=net_edge_bps,
            state=LifecycleState.NEW,
        )
    return existing.touch(as_of=as_of, edge_bps=edge_bps, net_edge_bps=net_edge_bps)


def expire_stale_states(
    states: dict[str, OpportunityState],
    now: datetime,
    limits: SessionLimits,
) -> None:
    ttl = timedelta(seconds=limits.ttl_seconds)
    to_delete: list[str] = []
    for opp_id, state in states.items():
        if now - state.last_seen >= ttl:
            to_delete.append(opp_id)
    for opp_id in to_delete:
        del states[opp_id]


__all__ = ["LifecycleState", "OpportunityState", "update_lifecycle", "expire_stale_states"]
