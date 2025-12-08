# Layer: core_math
# core/greeks.py
from __future__ import annotations

from dataclasses import dataclass
from math import log, sqrt, exp, erf, pi

from core.models import Position, CP


def _norm_cdf(x: float) -> float:
    """התפלגות נורמלית מצטברת N(x)."""
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


def _norm_pdf(x: float) -> float:
    """צפיפות נורמלית סטנדרטית φ(x)."""
    return (1.0 / sqrt(2.0 * pi)) * exp(-0.5 * x * x)


@dataclass
class Greeks:
    """Greeks לפוזיציה / אופציה בודדת."""

    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float


def _bs_greeks_single(
    S: float,
    K: float,
    T: float,
    r: float,
    q: float,
    sigma: float,
    cp: CP,
) -> Greeks:
    """
    Greeks לפי Black-Scholes לאופציה בודדת (ללא מכפיל / כמות).
    S – מחיר נכס בסיס
    K – סטרייק
    T – זמן בשנים
    r – ריבית חסרת סיכון (שנתית, כיחס)
    q – דיבידנד / תשואת נשיאה (שנתית, כיחס)
    sigma – סטיית תקן (IV) כיחס
    cp – "CALL" / "PUT"
    """
    if T <= 0.0 or sigma <= 0.0 or S <= 0.0 or K <= 0.0:
        return Greeks(0.0, 0.0, 0.0, 0.0, 0.0)

    sqrtT = sqrt(T)
    d1 = (log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT

    Nd1 = _norm_cdf(d1)
    Nd2 = _norm_cdf(d2)
    Nmd1 = _norm_cdf(-d1)
    Nmd2 = _norm_cdf(-d2)
    pdf = _norm_pdf(d1)

    disc_r = exp(-r * T)
    disc_q = exp(-q * T)

    if cp == "CALL":
        delta = disc_q * Nd1
        theta = (
            -S * disc_q * pdf * sigma / (2.0 * sqrtT)
            - r * K * disc_r * Nd2
            + q * S * disc_q * Nd1
        )
        rho = K * T * disc_r * Nd2
    else:  # PUT
        delta = -disc_q * Nmd1
        theta = (
            -S * disc_q * pdf * sigma / (2.0 * sqrtT)
            + r * K * disc_r * Nmd2
            - q * S * disc_q * Nmd1
        )
        rho = -K * T * disc_r * Nmd2

    gamma = disc_q * pdf / (S * sigma * sqrtT)
    vega = S * disc_q * pdf * sqrtT

    return Greeks(delta=delta, gamma=gamma, vega=vega, theta=theta, rho=rho)


def calc_position_greeks(
    position: Position,
    spot: float,
    dte_days: float,
    r: float,
    q: float,
    iv: float,
    multiplier: int = 1,
) -> Greeks:
    """
    Greeks לפוזיציה שלמה (כולל צד, כמות, מכפיל).
    r, q, iv ניתנים כיחס (למשל 0.02 = 2%).
    dte_days – ימים לפקיעה.

    תוצאה:
      delta/gamma – ביחידות "תחתון" * מכפיל
      vega       – שינוי בסכום (מאני) ל-1% שינוי ב-IV
      theta      – שינוי בסכום ליום (T+1)
      rho        – שינוי בסכום ל-1% שינוי בריבית
    """
    T = max(dte_days, 1e-6) / 365.0
    sigma = max(iv, 1e-6)

    total = Greeks(0.0, 0.0, 0.0, 0.0, 0.0)

    for leg in position.legs:
        side_sign = 1.0 if leg.side == "long" else -1.0

        g = _bs_greeks_single(
            S=spot,
            K=leg.strike,
            T=T,
            r=r,
            q=q,
            sigma=sigma,
            cp=leg.cp,
        )

        qty_factor = side_sign * float(leg.quantity) * float(multiplier)

        total.delta += g.delta * qty_factor
        total.gamma += g.gamma * qty_factor
        total.vega += g.vega * qty_factor
        total.theta += g.theta * qty_factor
        total.rho += g.rho * qty_factor

    # התאמה ליחידות "נוחות"
    total.vega /= 100.0  # פר 1% שינוי ב-IV
    total.rho /= 100.0  # פר 1% שינוי בריבית
    total.theta /= 365.0  # פר יום (T+1)

    return total
