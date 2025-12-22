from __future__ import annotations

from typing import Protocol

from core.pricing.context import PricingContext
from core.pricing.types import PriceResult


class PricingEngine(Protocol):
    def price_execution(self, execution: object, context: PricingContext) -> PriceResult:
        ...


__all__ = ["PricingEngine"]
