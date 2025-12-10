from __future__ import annotations

from typing import Dict

from core.adapters.contracts import PricingAdapter
from core.fx.contracts import FxConverter
from core.portfolio.models import Currency, MarketSnapshot, Money, Position


class BSPricingAdapter(PricingAdapter):
    """Placeholder for Black-Scholes-based pricing."""

    def price(self, position: Position, market: MarketSnapshot, fx_converter: FxConverter | None = None) -> Money:
        # TODO: implement Black-Scholes pricing
        raise NotImplementedError("Black-Scholes pricing not implemented yet.")


class PricingRouter:
    """Routes positions to appropriate pricing adapters based on instrument type."""

    def __init__(self, default_adapter: PricingAdapter | None = None):
        self._adapters: Dict[str, PricingAdapter] = {}
        self._default_adapter = default_adapter

    def register_adapter(self, instrument_type: str, adapter: PricingAdapter) -> None:
        self._adapters[instrument_type] = adapter

    def get_adapter(self, instrument_type: str) -> PricingAdapter:
        if instrument_type in self._adapters:
            return self._adapters[instrument_type]
        if self._default_adapter is not None:
            return self._default_adapter
        # TODO: introduce richer routing logic based on product metadata
        raise KeyError(f"No pricing adapter registered for instrument type '{instrument_type}'")

    def price(self, position: Position, market: MarketSnapshot, fx_converter: FxConverter | None = None) -> Money:
        adapter = self.get_adapter(position.instrument_type)
        return adapter.price(position, market, fx_converter=fx_converter)
