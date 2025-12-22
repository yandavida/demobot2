from __future__ import annotations

from dataclasses import dataclass

from core.market_data.types import MarketSnapshot
from core.portfolio.models import Currency


@dataclass(frozen=True)
class PricingContext:
    market: MarketSnapshot
    base_currency: Currency = "USD"


__all__ = ["PricingContext"]
