from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal
from core.portfolio.models import Currency

@dataclass(frozen=True)
class VarResult:
    """
    VaR reported as a positive loss amount in base currency
    """
    method: Literal["parametric", "historical"]
    confidence: float
    horizon_days: int
    currency: Currency
    var: float  # positive number representing loss threshold
    cvar: float | None = None  # filled in later (Stage 2.3)
    notes: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if self.var < 0:
            raise ValueError(f"var must be >= 0, got {self.var}")
