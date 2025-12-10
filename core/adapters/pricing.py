from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, TYPE_CHECKING

from core import greeks as core_greeks
from core import pricing as core_pricing
from core.adapters.contracts import PricingAdapter
from core.portfolio.models import MarketSnapshot, Money

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from core.models import Leg, Position

try:
    from core.portfolio.models import Currency
except Exception:  # pragma: no cover - fallback for current models
    Currency = str  # type: ignore[misc, assignment]


def _money(amount: float, ccy: Currency) -> Money:
    """Helper to construct Money regardless of the currency field name."""

    if hasattr(Money, "__dataclass_fields__") and "currency" in Money.__dataclass_fields__:
        return Money(amount=amount, currency=ccy)  # type: ignore[arg-type]
    return Money(amount=amount, ccy=ccy)  # type: ignore[arg-type]


@dataclass
class BSPricingAdapter(PricingAdapter):
    ccy: Currency = "USD"

    def price_leg(self, leg: "Leg", snapshot: MarketSnapshot) -> Money:
        symbol = getattr(leg, "symbol", None)
        if symbol is None:
            raise ValueError("Leg missing symbol for pricing")

        prices = getattr(snapshot, "prices", {}) or {}
        spot = prices.get(symbol)
        if spot is None and hasattr(snapshot, "get_price"):
            spot = snapshot.get_price(symbol)  # type: ignore[call-arg]
        if spot is None:
            raise ValueError(f"No spot price for symbol {symbol}")

        price_fn = getattr(core_pricing, "price_leg", None)
        if callable(price_fn):
            pv = price_fn(leg=leg, spot=spot, snapshot=snapshot)
        else:
            quantity = float(getattr(leg, "quantity", 1))
            side = getattr(leg, "side", "long")
            sign = 1.0 if side == "long" else -1.0
            premium = getattr(leg, "premium", None)
            pv = sign * quantity * float(premium if premium is not None else spot)

        return _money(amount=float(pv), ccy=self.ccy)

    def greeks_leg(self, leg: "Leg", snapshot: MarketSnapshot) -> Dict[str, float]:
        symbol = getattr(leg, "symbol", None)
        if symbol is None:
            raise ValueError("Leg missing symbol for greeks")

        prices = getattr(snapshot, "prices", {}) or {}
        spot = prices.get(symbol)
        if spot is None and hasattr(snapshot, "get_price"):
            spot = snapshot.get_price(symbol)  # type: ignore[call-arg]
        if spot is None:
            raise ValueError(f"No spot price for symbol {symbol}")

        greeks_fn = getattr(core_greeks, "calc_leg_greeks", None)
        if callable(greeks_fn):
            greeks = greeks_fn(leg=leg, spot=spot, snapshot=snapshot)
            return dict(greeks)

        totals = {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "rho": 0.0}
        return totals


@dataclass
class PricingRouter:
    default: PricingAdapter
    by_symbol: Dict[str, PricingAdapter] | None = None

    def _adapter_for_symbol(self, symbol: str | None) -> PricingAdapter:
        if symbol is not None and self.by_symbol and symbol in self.by_symbol:
            return self.by_symbol[symbol]
        return self.default

    def price_position(self, position: "Position", snapshot: MarketSnapshot) -> Money:
        legs = getattr(position, "legs", None)
        legs_iterable = legs if legs is not None else [position]

        total = 0.0
        for leg in legs_iterable:
            leg_symbol = getattr(leg, "symbol", getattr(position, "symbol", None))
            adapter = self._adapter_for_symbol(leg_symbol)
            leg_pv = adapter.price_leg(leg, snapshot)
            total += float(getattr(leg_pv, "amount", 0.0))

        ccy = getattr(position, "ccy", getattr(position, "currency", getattr(self.default, "ccy", "USD")))
        return _money(amount=total, ccy=ccy)

    def greeks_position(self, position: "Position", snapshot: MarketSnapshot) -> Dict[str, float]:
        legs = getattr(position, "legs", None)
        legs_iterable = legs if legs is not None else [position]

        totals: Dict[str, float] = {}
        for leg in legs_iterable:
            leg_symbol = getattr(leg, "symbol", getattr(position, "symbol", None))
            adapter = self._adapter_for_symbol(leg_symbol)
            g = adapter.greeks_leg(leg, snapshot)
            for k, v in g.items():
                totals[k] = totals.get(k, 0.0) + float(v)
        return totals

    # Backwards compatibility with the previous interface
    def price(self, position: "Position", market: MarketSnapshot, fx_converter=None):
        return self.price_position(position, market)
