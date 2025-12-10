from __future__ import annotations

from typing import Iterable, Protocol

from core.fx.contracts import FxConverter
from core.portfolio.models import MarketSnapshot, Money, Position


class MarketDataAdapter(Protocol):
    """Retrieves market data snapshots."""

    def get_snapshot(self, symbols: Iterable[str] | None = None) -> MarketSnapshot:
        ...


class PricingAdapter(Protocol):
    """Prices financial positions using market data."""

    def price(self, position: Position, market: MarketSnapshot, fx_converter: FxConverter | None = None) -> Money:
        ...
