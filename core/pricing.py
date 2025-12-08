# Layer: core_math
# core/pricing.py
from __future__ import annotations

from dataclasses import dataclass
from math import erf, exp, log, pi, sqrt
from typing import Literal

import numpy as np
import pandas as pd

from .models import IronCondorInput, IronCondorResult

# ============================================================
# חלק 1 – תמחור / מדדים ל-Iron Condor
# ============================================================


def mid_price(df: pd.DataFrame, strike: float, cp: str) -> float:
    """
    מאתר מחיר אופציה לפי סטרייק וסוג (CALL/PUT).
    מצפה לעמודות: 'strike', 'cp', 'price'.
    """
    row = df[(df["strike"] == strike) & (df["cp"] == cp)]
    if row.empty:
        raise ValueError(f"Missing price for {cp} @ {strike}")
    return float(row["price"].iloc[0])


def iron_condor_net_credit(df_view: pd.DataFrame, ic: IronCondorInput) -> float:
    """
    מחושב: (short PUT + short CALL) - (long PUT + long CALL)
    """
    price_sp = mid_price(df_view, ic.short_put_strike, "PUT")
    price_lp = mid_price(df_view, ic.long_put_strike, "PUT")
    price_sc = mid_price(df_view, ic.short_call_strike, "CALL")
    price_lc = mid_price(df_view, ic.long_call_strike, "CALL")
    return (price_sp + price_sc) - (price_lp + price_lc)


def iron_condor_metrics(df_view: pd.DataFrame, ic: IronCondorInput) -> IronCondorResult:
    """
    מחזיר קרדיט/דביט ליחידה, רווח/הפסד מקסימליים ונקודות איזון.
    בהגדרה כאן: רווח מקס' = הקרדיט, הפסד מקס' = הכנף הגרועה פחות הקרדיט.
    """
    net_credit = iron_condor_net_credit(df_view, ic)

    put_wing = abs(ic.short_put_strike - ic.long_put_strike)
    call_wing = abs(ic.long_call_strike - ic.short_call_strike)
    worst_wing = max(put_wing, call_wing)

    max_profit_per_unit = net_credit
    max_loss_per_unit = worst_wing - net_credit

    lower_be = ic.short_put_strike - net_credit
    upper_be = ic.short_call_strike + net_credit

    return IronCondorResult(
        net_credit=net_credit,
        max_profit_per_unit=max_profit_per_unit,
        max_loss_per_unit=max_loss_per_unit,
        lower_be=lower_be,
        upper_be=upper_be,
    )


def iron_condor_expiry_payoff_curve(
    df_view: pd.DataFrame,
    ic: IronCondorInput,
    n_points: int = 300,
    x_pad: float = 0.10,
) -> pd.DataFrame:
    """
    payoff ביום פקיעה ל-IC על פני טווח מחירים סביב הספוט/סטרייקים.
    מחזיר DataFrame עם עמודות: S, P/L (לכל החוזים יחד לפי qty*multiplier).
    """
    # טווח S
    s_min = min(
        ic.long_put_strike,
        ic.short_put_strike,
        ic.short_call_strike,
        ic.long_call_strike,
        ic.spot,
    )
    s_max = max(
        ic.long_put_strike,
        ic.short_put_strike,
        ic.short_call_strike,
        ic.long_call_strike,
        ic.spot,
    )
    span = s_max - s_min
    s_min = s_min - x_pad * span
    s_max = s_max + x_pad * span
    S = np.linspace(s_min, s_max, n_points)

    # מחירים לכל רגל
    sp = mid_price(df_view, ic.short_put_strike, "PUT")
    lp = mid_price(df_view, ic.long_put_strike, "PUT")
    sc = mid_price(df_view, ic.short_call_strike, "CALL")
    lc = mid_price(df_view, ic.long_call_strike, "CALL")

    # payoff לא מחושב דרך BSM כאן – רק ערך פנימי בפקיעה פחות פרמיה ששולמה/נתקבלה
    def payoff_put(k: float, price: float, short: bool) -> np.ndarray:
        intrinsic = np.maximum(k - S, 0.0)
        leg = (price - intrinsic) if short else (intrinsic - price)
        return leg

    def payoff_call(k: float, price: float, short: bool) -> np.ndarray:
        intrinsic = np.maximum(S - k, 0.0)
        leg = (price - intrinsic) if short else (intrinsic - price)
        return leg

    pl = (
        (
            payoff_put(ic.short_put_strike, sp, short=True)
            + payoff_put(ic.long_put_strike, lp, short=False)
            + payoff_call(ic.short_call_strike, sc, short=True)
            + payoff_call(ic.long_call_strike, lc, short=False)
        )
        * ic.qty
        * ic.multiplier
    )

    return pd.DataFrame({"S": S, "P/L": pl})


# ============================================================
# חלק 2 – Black–Scholes price + Greeks
# ============================================================

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
    # CDF דרך erf — ללא תלות בספריות חיצוניות
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


def _sanitize_sigma_T(sigma: float, T: float) -> tuple[float, float]:
    sigma = max(1e-8, float(sigma))
    T = max(1e-8, float(T))
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

    # S * exp((r - q) * T)  # שורה מיותרת, נשארת כאן לשימור לוגיקה קיימת
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

    return BSResult(
        price=float(price),
        delta=float(delta),
        gamma=float(gamma),
        theta=float(theta),
        vega=float(vega / 100.0),  # נוח כחלק ל־1% שינוי ב־IV
        rho=float(rho / 100.0),  # נוח כחלק ל־1% שינוי ב־r
    )
