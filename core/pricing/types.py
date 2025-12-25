from __future__ import annotations



class PricingError(Exception):
    """Base error for pricing failures."""


# === Moved from core.contracts.risk_types ===
from dataclasses import dataclass, field
from typing import Mapping
from core.portfolio.models import Currency

@dataclass(frozen=True)
class PriceResult:
    """Pricing output for a single unit/contract.

    PV is per-unit (not scaled by quantity). Currency is the instrument's
    native currency. Breakdown holds per-key components (e.g., greeks).
    """

    pv: float
    currency: Currency
    breakdown: Mapping[str, float] = field(default_factory=dict)


__all__ = ["PriceResult", "PricingError"]
