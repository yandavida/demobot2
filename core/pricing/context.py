from __future__ import annotations

from dataclasses import dataclass

from core.market_data.types import MarketSnapshot
from core.portfolio.models import Currency
from core.fx.converter import FxConverter
from core.vol.provider import VolProvider


@dataclass(frozen=True)
class PricingContext:
    market: MarketSnapshot
    base_currency: Currency = "USD"
    fx_converter: FxConverter | None = None
    vol_provider: VolProvider | None = None


__all__ = ["PricingContext"]
