from __future__ import annotations

from typing import Mapping

from core.finance.market import MarketSnapshot
from core.market_data.types import PriceQuote, FxRateQuote
from core.pricing.context import PricingContext
from core.scenarios.types import Scenario, Shock
from core.fx.errors import MissingFxRateError
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

    # apply FX shocks
    fx_shocks: Mapping[str, float] = {p: m for p, m in scenario.fx_shocks_by_pair}
    new_fx: list[FxRateQuote] = []

    # Build lookup for existing pairs for quick access
    existing = {f.pair: float(f.rate) for f in snapshot.fx_rates}

    # apply multiplicative updates where possible; if a pair is missing but inverse present,
    # adjust inverse accordingly. If neither present and strict behavior is expected, raise.
    for f in snapshot.fx_rates:
        pair = f.pair
        rate = float(f.rate)
        if pair in fx_shocks:
            mult = float(fx_shocks[pair])
            new_rate = rate * mult
        else:
            # check inverse
            a, b = pair.split("/", 1)
            inv = f"{b}/{a}"
            if inv in fx_shocks:
                mult = float(fx_shocks[inv])
                # if inverse shocked by mult, the current pair rate is divided by mult
                new_rate = rate / mult
            else:
                new_rate = rate

        if new_rate <= 0.0:
            raise ValueError(f"invalid shocked fx rate for {pair}: {new_rate}")
        new_fx.append(FxRateQuote(pair=pair, rate=float(new_rate)))

    # If scenario provided shocks for pairs not present in snapshot, enforce strict behavior
    missing_pairs = [p for p, _ in scenario.fx_shocks_by_pair if p not in existing and (p.split('/',1)[1] + '/' + p.split('/',1)[0]) not in existing]
    if missing_pairs:
        # reuse existing fx error type
        raise MissingFxRateError(f"FX rate(s) for {missing_pairs} not found in snapshot")

    # deterministic ordering enforced by MarketSnapshot
    return MarketSnapshot(quotes=tuple(new_quotes), fx_rates=tuple(new_fx), as_of=snapshot.as_of)


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
