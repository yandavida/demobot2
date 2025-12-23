from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from core.portfolio.models import Currency

@dataclass(frozen=True)
class RiskContext:
    horizon_days: int
    confidence: float
    base_currency: Currency
    as_of: Optional[date | datetime] = None
    notes: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if self.horizon_days not in (1, 10):
            raise ValueError(f"horizon_days must be 1 or 10, got {self.horizon_days}")
        if not (0.90 <= self.confidence <= 0.9999):
            raise ValueError(f"confidence must be between 0.90 and 0.9999, got {self.confidence}")


def default_risk_context() -> RiskContext:
    return RiskContext(horizon_days=1, confidence=0.99, base_currency="ILS")
