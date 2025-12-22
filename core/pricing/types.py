from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from core.portfolio.models import Currency


@dataclass(frozen=True)
class PriceResult:
    pv: float
    currency: Currency
    breakdown: Mapping[str, float] = field(default_factory=dict)


class PricingError(Exception):
    """Base error for pricing failures."""


__all__ = ["PriceResult", "PricingError"]
