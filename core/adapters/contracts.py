from __future__ import annotations

from typing import Any, Dict, Iterable, Protocol

from core.portfolio.models import MarketSnapshot, Money


class MarketDataAdapter(Protocol):
    """Retrieves market data snapshots."""

    def get_snapshot(self, symbols: Iterable[str] | None = None) -> MarketSnapshot:
        ...


class PricingAdapter(Protocol):
    """Pricing and Greeks for a single leg."""

    def price_leg(self, leg: Any, snapshot: MarketSnapshot) -> Money:
        ...

    def greeks_leg(self, leg: Any, snapshot: MarketSnapshot) -> Dict[str, float]:
        ...
