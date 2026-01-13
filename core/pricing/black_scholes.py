from math import erf, exp, log, pi, sqrt
from core.numeric_policy import DEFAULT_TOLERANCES, MetricClass
from dataclasses import dataclass
from typing import Literal
from core.pricing.units import to_canonical_greeks

CallPut = Literal["C", "P"]  # "C"=Call, "P"=Put

@dataclass
class BSResult:
    price: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float

def _norm_pdf(x: float) -> float:
    return exp(-0.5 * x * x) / sqrt(2.0 * pi)

def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))

def _sanitize_sigma_T(sigma: float, T: float) -> tuple[float, float]:
    # Use numeric policy defaults instead of hardcoded small constants
    min_sigma = DEFAULT_TOLERANCES[MetricClass.VOL].abs
    min_T = DEFAULT_TOLERANCES[MetricClass.TIME].abs

    sigma = max(min_sigma, float(sigma))
    T = max(min_T, float(T))
    return sigma, T

def bs_price_greeks(
    S: float,
    K: float,
    r: float,
    q: float,
    sigma: float,
    T: float,
    cp: CallPut,
) -> BSResult:
    """
    Black-Scholes עם דיבידנד רציף q.
    S: spot, K: strike, r: risk-free (שנתי), q: dividend yield (שנתי)
    sigma: סטיית תקן גלומה (שנתית), T: זמן בשנים, cp: "C" או "P"
    """
    sigma, T = _sanitize_sigma_T(sigma, T)
    if S <= 0 or K <= 0:
        return BSResult(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    vol_sqrtT = sigma * sqrt(T)
    d1 = (log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / vol_sqrtT
    d2 = d1 - vol_sqrtT

    Nd1 = _norm_cdf(d1)
    Nd2 = _norm_cdf(d2)
    nd1 = _norm_pdf(d1)

    disc_r = exp(-r * T)
    disc_q = exp(-q * T)

    if cp == "C":
        price = S * disc_q * Nd1 - K * disc_r * Nd2
        delta = disc_q * Nd1
        rho = K * T * disc_r * Nd2
        theta = (
            -(S * disc_q * nd1 * sigma) / (2 * sqrt(T))
            - r * K * disc_r * Nd2
            + q * S * disc_q * Nd1
        )
    else:  # Put
        Nmd1 = _norm_cdf(-d1)
        Nmd2 = _norm_cdf(-d2)
        price = K * disc_r * Nmd2 - S * disc_q * Nmd1
        delta = -disc_q * Nmd1
        rho = -K * T * disc_r * Nmd2
        theta = (
            -(S * disc_q * nd1 * sigma) / (2 * sqrt(T))
            + r * K * disc_r * Nmd2
            - q * S * disc_q * Nmd1
        )

    gamma = (disc_q * nd1) / (S * vol_sqrtT)
    vega = S * disc_q * nd1 * sqrt(T)

    greeks = {
        'delta': float(delta),
        'gamma': float(gamma),
        'theta': float(theta),
        'vega': float(vega),
        'rho': float(rho),
    }
    canon = to_canonical_greeks(greeks)
    return BSResult(
        price=float(price),
        delta=canon['delta'],
        gamma=canon['gamma'],
        theta=canon['theta'],
        vega=canon['vega'],
        rho=canon['rho'],
    )
