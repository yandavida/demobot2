from __future__ import annotations

from typing import Protocol

from core.market_data.types import AssetId, PriceQuote, FxRateQuote, MarketSnapshot


class MarketDataProvider(Protocol):
    def get_price(self, asset: AssetId) -> PriceQuote:
        ...

    def has_price(self, asset: AssetId) -> bool:
        ...

    def get_fx_rate(self, pair: str) -> FxRateQuote:
        ...

    def has_fx_rate(self, pair: str) -> bool:
        ...

    def snapshot(self) -> MarketSnapshot:
        ...


__all__ = ["MarketDataProvider"]
