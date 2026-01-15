from __future__ import annotations

from typing import Dict

from core.pricing.engines.binomial_american import price_american_binomial_crr
from core.pricing.inputs import PricingInput
from core.numeric_policy import DEFAULT_TOLERANCES, MetricClass


def _round_cents(x: float) -> float:
    # deterministic rounding to cents (two decimals)
    return float(round(x, 2))


def american_price_greeks_fd(
    *,
    s: float,
    k: float,
    t: float,
    sigma: float,
    r: float = 0.0,
    q: float = 0.0,
    is_call: bool = True,
    steps: int = 1000,
) -> Dict[str, float]:
    """Deterministic FD greeks for American options using the binomial engine.

    Returns a dict: {"price", "delta", "gamma", "vega", "theta", "rho"}.
    Units: vega per 1% IV, theta per day.
    """
    # SSOT tolerances
    vol_floor = DEFAULT_TOLERANCES[MetricClass.VOL].abs or 0.0
    time_floor = DEFAULT_TOLERANCES[MetricClass.TIME].abs or 0.0

    # deterministic FD step choices
    hS = max(_round_cents(s * 0.001), 0.01)
    hV = 0.001
    hT = 1.0 / 365.0
    hR = 0.0001

    # clamp vol bumps to remain positive
    low_sigma = max(sigma - hV, vol_floor)
    high_sigma = sigma + hV

    def _price(spot: float, vol: float, tt: float, rate: float) -> float:
        inp = PricingInput(float(spot), float(k), float(tt), float(rate), float(q), float(vol), bool(is_call))
        return price_american_binomial_crr(inp, steps=steps)

    price0 = _price(s, sigma, t, r)

    # Delta & Gamma (central differences)
    p_sp_plus = _price(s + hS, sigma, t, r)
    p_sp_minus = _price(s - hS, sigma, t, r)
    delta = (p_sp_plus - p_sp_minus) / (2.0 * hS)
    gamma = (p_sp_plus - 2.0 * price0 + p_sp_minus) / (hS * hS)

    # Vega (central diff) -- per unit vol, convert to per 1% by dividing by 100
    p_vol_plus = _price(s, high_sigma, t, r)
    p_vol_minus = _price(s, low_sigma, t, r)
    vega_abs = (p_vol_plus - p_vol_minus) / (2.0 * hV)
    vega = vega_abs / 100.0

    # Theta: approximate derivative w.r.t. time to expiry with sign matching BS convention
    if t > hT + time_floor:
        p_t_minus = _price(s, sigma, max(t - hT, 0.0), r)
        # derivative dP/dt (time to expiry): (P(t-h) - P(t)) / h -> typically negative
        theta_abs = (p_t_minus - price0) / hT
    else:
        p_t_plus = _price(s, sigma, t + hT, r)
        # short-dated: use forward approximation with sign flip to keep negative convention
        theta_abs = (price0 - p_t_plus) / hT
    theta = theta_abs / 365.0

    # Rho (central diff)
    p_r_plus = _price(s, sigma, t, r + hR)
    p_r_minus = _price(s, sigma, t, max(r - hR, -1.0))
    rho = (p_r_plus - p_r_minus) / (2.0 * hR)

    return {
        "price": float(price0),
        "delta": float(delta),
        "gamma": float(gamma),
        "vega": float(vega),
        "theta": float(theta),
        "rho": float(rho),
    }


__all__ = ["american_price_greeks_fd"]
