from __future__ import annotations

import math
from typing import Mapping, Any

from core.pricing.types import PriceResult, PricingError
from core.pricing.option_types import EuropeanOption
from core.vol.provider import VolProvider
from core.pricing.context import PricingContext


SQRT2 = math.sqrt(2.0)
SQRT_2PI = math.sqrt(2.0 * math.pi)


def norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / SQRT_2PI


def norm_cdf(x: float) -> float:
    # stable using erf
    return 0.5 * (1.0 + math.erf(x / SQRT2))


def _d1(spot: float, strike: float, rate: float, div: float, vol: float, t: float) -> float:
    if t <= 0 or vol <= 0:
        raise ValueError("d1 not defined for t<=0 or vol<=0")
    return (math.log(spot / strike) + (rate - div + 0.5 * vol * vol) * t) / (vol * math.sqrt(t))


def _d2(d1: float, vol: float, t: float) -> float:
    return d1 - vol * math.sqrt(t)


def bs_price(option_type: str, spot: float, strike: float, rate: float, div: float, vol: float, t: float) -> float:
    # per-unit price
    if t <= 0:
        # immediate intrinsic
        if option_type == "call":
            return max(spot - strike, 0.0)
        return max(strike - spot, 0.0)

    if vol <= 0:
        # deterministic forward intrinsic: PV = max(S e^{-q t} - K e^{-r t}, 0)
        forward_pv = spot * math.exp(-div * t) - strike * math.exp(-rate * t)
        if option_type == "call":
            return max(forward_pv, 0.0)
        return max(-forward_pv, 0.0)

    d1 = _d1(spot, strike, rate, div, vol, t)
    d2 = _d2(d1, vol, t)

    df_r = math.exp(-rate * t)
    df_q = math.exp(-div * t)

    if option_type == "call":
        return spot * df_q * norm_cdf(d1) - strike * df_r * norm_cdf(d2)
    return strike * df_r * norm_cdf(-d2) - spot * df_q * norm_cdf(-d1)


def _req_float(v: Any, name: str) -> float:
    if v is None:
        raise TypeError(f"bs_greeks() missing required input: {name}")
    if isinstance(v, (int, float, str)):
        return float(v)
    raise TypeError(f"bs_greeks() invalid type for {name}: {type(v).__name__}")

def bs_greeks(*args, **kwargs) -> Mapping[str, float]:
    """
    Canonical BS greeks adapter.
    Public contract: cp in {"C","P"}.
    Internal math uses resolved option_type.
    Supports both legacy positional and canonical keyword-only API.

    LOCKED CONTRACT:
    - Only European options supported. American options are unsupported and must raise.
    - Vega is returned per +1% IV (0.01 vol).
    - Theta is returned per 1 day.
    - No distributed normalization: all unit normalization is via core/pricing/units.py.
    - FX Forward sign convention: BUY_BASE = notional * (spot - forward), SELL_BASE = -notional * (spot - forward).
    """
    # Legacy positional: (option_type, spot, strike, rate, div, vol, t)
    if args:
        if len(args) != 7:
            raise TypeError(f"bs_greeks() legacy positional expects 7 args, got {len(args)}")
        option_type, spot, strike, rate, div, vol, t = args
        # Map legacy option_type to cp
        if option_type.lower() in ("call", "c"):
            cp = "C"
        elif option_type.lower() in ("put", "p"):
            cp = "P"
        else:
            raise ValueError(f"Invalid option_type: {option_type!r}")
        # Recurse to canonical
        return bs_greeks(spot=spot, strike=strike, t=t, rate=rate, div=div, vol=vol, cp=cp)

    # Canonical keyword-only
    spot_obj = kwargs.get("spot")
    strike_obj = kwargs.get("strike")
    t_obj = kwargs.get("t")
    rate_obj = kwargs.get("rate")
    div_obj = kwargs.get("div")
    vol_obj = kwargs.get("vol")

    spot = _req_float(kwargs.get("spot"), "spot")
    strike = _req_float(kwargs.get("strike"), "strike")
    t = _req_float(kwargs.get("t"), "t")
    rate = _req_float(kwargs.get("rate"), "rate")
    div = _req_float(kwargs.get("div"), "div")
    vol = _req_float(kwargs.get("vol"), "vol")
    cp_raw = kwargs.get("cp")
    option_type_raw = kwargs.get("option_type")
    opt = cp_raw if cp_raw is not None else option_type_raw
    if opt is None:
        raise TypeError("Either cp or option_type must be provided.")
    opt_s = str(opt)
    if opt_s not in ("C", "P"):
        raise ValueError(f"Invalid option type: {opt!r}. Expected 'C' or 'P'.")
    option_type = opt_s

    # --- DO NOT CHANGE ANY MATH BELOW THIS LINE ---
    if t <= 0:
        # intrinsic at expiry
        if option_type == "C":
            delta = 1.0 if spot > strike else 0.0
        else:
            delta = -1.0 if spot < strike else 0.0
        return {"delta": delta, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0}

    if vol <= 0:
        # deterministic: delta is e^{-q t} if in-the-money forward, else 0 (call)
        forward = spot * math.exp((rate - div) * t)
        if option_type == "C":
            if forward > strike:
                return {"delta": math.exp(-div * t), "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0}
            return {"delta": 0.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0}
        else:
            if forward < strike:
                return {"delta": -math.exp(-div * t), "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0}
            return {"delta": 0.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0}

    d1 = _d1(spot, strike, rate, div, vol, t)
    d2 = _d2(d1, vol, t)

    df_r = math.exp(-rate * t)
    df_q = math.exp(-div * t)

    pdf_d1 = norm_pdf(d1)

    delta = df_q * norm_cdf(d1) if option_type == "C" else df_q * (norm_cdf(d1) - 1.0)
    gamma = df_q * pdf_d1 / (spot * vol * math.sqrt(t))
    vega = spot * df_q * pdf_d1 * math.sqrt(t)

    # theta per year
    theta = - (spot * df_q * pdf_d1 * vol) / (2.0 * math.sqrt(t)) - rate * strike * df_r * (norm_cdf(d2) if option_type == "C" else -norm_cdf(-d2)) + div * spot * df_q * (norm_cdf(d1) if option_type == "C" else (norm_cdf(d1) - 1.0))

    # rho
    rho = strike * t * df_r * (norm_cdf(d2) if option_type == "C" else -norm_cdf(-d2))

    return {"delta": float(delta), "gamma": float(gamma), "vega": float(vega), "theta": float(theta), "rho": float(rho)}


class BlackScholesPricingEngine:
    """Pricing engine for European options using Black-Scholes formulas.

    Expects `execution` to be either `EuropeanOption` or an object with compatible attributes.
    Returns `PriceResult` with pv per unit and breakdown containing greeks.
    """

    def price_execution(self, execution: object, context: PricingContext) -> PriceResult:
        # Accept EuropeanOption directly
        if isinstance(execution, EuropeanOption):
            opt = execution
            spot = None
            # locate spot in market snapshot
            for q in context.market.quotes:
                if q.asset == opt.underlying:
                    spot = q.price
                    break
            if spot is None:
                raise PricingError(f"missing spot for {opt.underlying}")

            # Prefer vol from `PricingContext.vol_provider` when available.
            # Compatibility: tolerate context-like objects by using getattr,
            # but tests and callers should pass `PricingContext`. This
            # tolerance is temporary and exists for backward compatibility.
            vol = None
            vp_ctx = getattr(context, "vol_provider", None)
            if vp_ctx is not None:
                vp1: VolProvider = vp_ctx
                vol = vp1.get_vol(
                    underlying=opt.underlying,
                    expiry_t=float(opt.expiry_t),
                    strike=float(opt.strike),
                    option_type=opt.option_type,
                    strict=True,
                )
            else:
                vol = getattr(opt, "vol", None)
            if vol is None:
                raise PricingError("Missing vol input")

            price = bs_price(opt.option_type, spot, opt.strike, 0.0, 0.0, float(vol), float(opt.expiry_t))
            greeks = bs_greeks(opt.option_type, spot, opt.strike, 0.0, 0.0, float(vol), float(opt.expiry_t))
            # apply contract multiplier
            mult = float(opt.contract_multiplier)
            pv = float(price) * mult
            breakdown = {k: float(v) for k, v in greeks.items()}
            return PriceResult(pv=pv, currency=opt.currency, breakdown=breakdown)

        # else: try to extract fields
        try:
            underlying = getattr(execution, "underlying")
            strike = float(getattr(execution, "strike"))
            opttype = getattr(execution, "option_type")
            expiry_t = float(getattr(execution, "expiry_t"))
        except Exception:
            raise PricingError("unsupported execution type for BlackScholesPricingEngine")

        # resolve vol: prefer provider if available, else take execution.vol
        # Compatibility: prefer `PricingContext.vol_provider` but tolerate
        # context-like objects (getattr) for backwards compatibility.
        vol = None
        vp_ctx2 = getattr(context, "vol_provider", None)
        if vp_ctx2 is not None:
            vp2: VolProvider = vp_ctx2
            vol = vp2.get_vol(
                underlying=underlying,
                expiry_t=expiry_t,
                strike=strike,
                option_type=opttype,
                strict=True,
            )
        else:
            vol = getattr(execution, "vol", None)
        if vol is None:
            raise PricingError("Missing vol input")

        spot = None
        for q in context.market.quotes:
            if q.asset == underlying:
                spot = q.price
                break
        if spot is None:
            raise PricingError(f"missing spot for {underlying}")

        price = bs_price(opttype, spot, strike, 0.0, 0.0, float(vol), expiry_t)
        greeks = bs_greeks(opttype, spot, strike, 0.0, 0.0, float(vol), expiry_t)
        return PriceResult(pv=float(price), currency=getattr(execution, "currency", "USD"), breakdown={k: float(v) for k, v in greeks.items()})


__all__ = ["bs_price", "bs_greeks", "BlackScholesPricingEngine"]
