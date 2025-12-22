from __future__ import annotations

import math
from typing import Mapping

from core.pricing.types import PriceResult, PricingError
from core.pricing.option_types import EuropeanOption


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


def bs_greeks(option_type: str, spot: float, strike: float, rate: float, div: float, vol: float, t: float) -> Mapping[str, float]:
    # return per-unit greeks
    # handle boundaries
    if t <= 0:
        # intrinsic at expiry
        if option_type == "call":
            delta = 1.0 if spot > strike else 0.0
        else:
            delta = -1.0 if spot < strike else 0.0
        return {"delta": delta, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0}

    if vol <= 0:
        # deterministic: delta is e^{-q t} if in-the-money forward, else 0 (call)
        forward = spot * math.exp((rate - div) * t)
        if option_type == "call":
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

    delta = df_q * norm_cdf(d1) if option_type == "call" else df_q * (norm_cdf(d1) - 1.0)
    gamma = df_q * pdf_d1 / (spot * vol * math.sqrt(t))
    vega = spot * df_q * pdf_d1 * math.sqrt(t)

    # theta per year
    theta = - (spot * df_q * pdf_d1 * vol) / (2.0 * math.sqrt(t)) - rate * strike * df_r * (norm_cdf(d2) if option_type == "call" else -norm_cdf(-d2)) + div * spot * df_q * (norm_cdf(d1) if option_type == "call" else (norm_cdf(d1) - 1.0))

    # rho
    rho = strike * t * df_r * (norm_cdf(d2) if option_type == "call" else -norm_cdf(-d2))

    return {"delta": float(delta), "gamma": float(gamma), "vega": float(vega), "theta": float(theta), "rho": float(rho)}


class BlackScholesPricingEngine:
    """Pricing engine for European options using Black-Scholes formulas.

    Expects `execution` to be either `EuropeanOption` or an object with compatible attributes.
    Returns `PriceResult` with pv per unit and breakdown containing greeks.
    """

    def price_execution(self, execution: object, context: object) -> PriceResult:
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

            vol = getattr(opt, "vol", None)
            # allow vol provided on option or passed separately via context.market (not available yet)
            if vol is None:
                raise PricingError("option missing vol parameter")

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
            vol = float(getattr(execution, "vol"))
        except Exception:
            raise PricingError("unsupported execution type for BlackScholesPricingEngine")

        spot = None
        for q in context.market.quotes:
            if q.asset == underlying:
                spot = q.price
                break
        if spot is None:
            raise PricingError(f"missing spot for {underlying}")

        price = bs_price(opttype, spot, strike, 0.0, 0.0, vol, expiry_t)
        greeks = bs_greeks(opttype, spot, strike, 0.0, 0.0, vol, expiry_t)
        return PriceResult(pv=float(price), currency=getattr(execution, "currency", "USD"), breakdown={k: float(v) for k, v in greeks.items()})


__all__ = ["bs_price", "bs_greeks", "BlackScholesPricingEngine"]
