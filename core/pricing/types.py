from __future__ import annotations

from core.contracts.risk_types import PriceResult


class PricingError(Exception):
    """Base error for pricing failures."""


__all__ = ["PriceResult", "PricingError"]
