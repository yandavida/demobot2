from __future__ import annotations

from typing import Mapping

from core.market_data.types import MarketSnapshot, PriceQuote
from core.pricing.context import PricingContext
from core.scenarios.types import Scenario, Shock
from core.vol.provider import VolProvider


def apply_shock_to_snapshot(snapshot: MarketSnapshot, scenario: Scenario) -> MarketSnapshot:
    # Build mapping of shocks
    shocks: Mapping[str, Shock] = {k: v for k, v in scenario.shocks_by_symbol}

    new_quotes = []
    for q in snapshot.quotes:
        sh = shocks.get(q.asset)
        if sh is None:
            new_quotes.append(q)
        else:
            new_price = float(q.price) * (1.0 + float(sh.spot_pct))
            new_quotes.append(PriceQuote(asset=q.asset, price=new_price, currency=q.currency))

    return MarketSnapshot(quotes=tuple(new_quotes), fx_rates=tuple(snapshot.fx_rates), as_of=snapshot.as_of)


class ShockedVolProvider(VolProvider):
    def __init__(self, base: VolProvider | None, shocks: Mapping[str, Shock]):
        self._base = base
        self._shocks = dict(shocks)

    def get_vol(self, *, underlying: str, expiry_t: float, strike: float, option_type: str, strict: bool = True) -> float:
        base_vol = None
        if self._base is not None:
            base_vol = self._base.get_vol(underlying=underlying, expiry_t=expiry_t, strike=strike, option_type=option_type, strict=strict)
        if base_vol is None:
            if strict:
                raise ValueError("missing base vol")
            base_vol = 0.0

        sh = self._shocks.get(underlying)
        vol = float(base_vol)
        if sh is not None:
            vol = vol + float(sh.vol_abs)
            vol = vol * (1.0 + float(sh.vol_pct))
        if vol < 0.0:
            vol = 0.0
        return float(vol)


def build_shocked_context(base_context: PricingContext, scenario: Scenario) -> PricingContext:
    # Build shocked market snapshot
    shocked_market = apply_shock_to_snapshot(base_context.market, scenario)

    # Build shocked vol provider
    shocks_map = {k: v for k, v in scenario.shocks_by_symbol}
    base_vp = getattr(base_context, "vol_provider", None)
    shocked_vp = ShockedVolProvider(base=base_vp, shocks=shocks_map)

    return PricingContext(market=shocked_market, base_currency=base_context.base_currency, fx_converter=base_context.fx_converter, vol_provider=shocked_vp)


__all__ = ["apply_shock_to_snapshot", "ShockedVolProvider", "build_shocked_context"]
