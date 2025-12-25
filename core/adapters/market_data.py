from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from core.adapters.contracts import MarketDataAdapter
from core.market_data.types import MarketSnapshot, PriceQuote


@dataclass
class InMemoryMarketDataAdapter(MarketDataAdapter):
    prices: Mapping[str, float] = field(default_factory=dict)

    def get_snapshot(self, symbols: Iterable[str] | None = None) -> MarketSnapshot:
        if symbols is None:
            snapshot_prices = dict(self.prices)
        else:
            requested = set(symbols)
            snapshot_prices = {symbol: price for symbol, price in self.prices.items() if symbol in requested}
        # המרה ל-PriceQuote לפי החוזה הקנוני
        quotes = tuple(
            PriceQuote(asset=symbol, price=price, currency="USD")  # TODO: יש להחליף ל-currency אמיתי אם קיים
            for symbol, price in snapshot_prices.items()
        )
        return MarketSnapshot(quotes=quotes)
