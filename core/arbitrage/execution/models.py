from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ExecutionConstraints:
    min_edge_bps: float
    max_spread_bps: float
    max_age_ms: int
    max_notional: float
    max_quantity: float
    max_latency_ms: int
    allowed_venues: set[str] | None = None
    conservative_by_default: bool = True


@dataclass
class ExecutionDecision:
    can_execute: bool
    recommended_qty: float
    ts: datetime
    reason_codes: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
