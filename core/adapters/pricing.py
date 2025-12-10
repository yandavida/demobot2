from __future__ import annotations

from typing import Dict

from core.adapters.contracts import PricingAdapter
from core.fx.contracts import FxConverter
from core.portfolio.models import MarketSnapshot, Money, Position


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

    def get_adapter(self, instrument_type: str | None) -> PricingAdapter:
        if instrument_type is not None and instrument_type in self._adapters:
            return self._adapters[instrument_type]
        if self._default_adapter is not None:
            return self._default_adapter
        raise KeyError("No pricing adapter available for the provided position.")

    def price(self, position: Position, market: MarketSnapshot, fx_converter: FxConverter | None = None) -> Money:
        instrument_type = getattr(position, "instrument_type", None)
        adapter = self.get_adapter(instrument_type)
        return adapter.price(position, market, fx_converter=fx_converter)
