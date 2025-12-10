from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from core.adapters.contracts import MarketDataAdapter
from core.portfolio.models import Currency, MarketSnapshot


@dataclass
class InMemoryMarketDataAdapter(MarketDataAdapter):
    prices: Mapping[str, float] = field(default_factory=dict)

    def get_snapshot(self, symbols: Iterable[str] | None = None) -> MarketSnapshot:
        if symbols is None:
            snapshot_prices = dict(self.prices)
        else:
            requested = set(symbols)
            snapshot_prices = {symbol: price for symbol, price in self.prices.items() if symbol in requested}
        usd = Currency("USD")
        return MarketSnapshot(spot=snapshot_prices, rates={usd: 1.0}, iv={})
