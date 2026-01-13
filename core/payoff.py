# Layer: core_math
# core/payoff.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Dict

import numpy as np
import pandas as pd

from .models import Leg, Position


# ===== חישוב P/L לרגל אחת =====


def payoff_leg(leg: Leg, underlying_price: float) -> float:
    """
    חישוב רווח/הפסד לרגל אחת, למחיר נכס נתון.

    convention:
    - long CALL/PUT → intrinsic - premium
    - short CALL/PUT → premium - intrinsic
    """
    # intrinsic value
    if leg.cp == "CALL":
        intrinsic = max(0.0, underlying_price - leg.strike)
    else:  # "PUT"
        intrinsic = max(0.0, leg.strike - underlying_price)

    if leg.side == "long":
        pl_per_contract = intrinsic - leg.premium
    else:  # "short"
        pl_per_contract = leg.premium - intrinsic

    return pl_per_contract * leg.quantity


def payoff_position(position: Position, underlying_price: float) -> float:
    """סכימת ה־P/L של כל הרגליים בפוזיציה."""
    return sum(payoff_leg(leg, underlying_price) for leg in position.legs)


# ===== עקומת P/L =====


@dataclass
class PayoffCurve:
    prices: np.ndarray
    pl: np.ndarray

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame({"price": self.prices, "pl": self.pl})


def generate_price_range(
    center_price: float,
    lower_factor: float = 0.8,
    upper_factor: float = 1.2,
    num_points: int = 201,
) -> np.ndarray:
    """
    יצירת טווח מחירים סביב מחיר מרכזי (למשל מחיר נכס נוכחי).
    לדוגמה: 0.8x עד 1.2x עם 201 נקודות.
    """
    low = center_price * lower_factor
    high = center_price * upper_factor
    return np.linspace(low, high, num_points)


def generate_payoff_curve(
    position: Position,
    prices: Iterable[float],
) -> PayoffCurve:
    """
    חישוב עקומת P/L לכל טווח מחירים נתון.
    """
    prices_arr = np.array(list(prices), dtype=float)
    pl_arr = np.array(
        [payoff_position(position, p) for p in prices_arr],
        dtype=float,
    )
    return PayoffCurve(prices=prices_arr, pl=pl_arr)


# ===== מקס רווח / הפסד / נקודות BE =====


def calc_max_profit(curve: PayoffCurve) -> float:
    """מקסימום רווח מתוך העקומה."""
    return float(curve.pl.max())


def calc_max_loss(curve: PayoffCurve) -> float:
    """מקסימום הפסד (ערך מינימלי בעקומה)."""
    return float(curve.pl.min())


def calc_break_even_points(curve: PayoffCurve, tol: float | None = None) -> List[float]:
    """
    חישוב נקודות איזון (Break Even) כנקודות שבהן P/L חוצה את 0.

    נעשה אינטרפולציה ליניארית בין נקודות סמוכות שמשנות סימן.
    """
    from core.numeric_policy import DEFAULT_TOLERANCES, MetricClass

    # Resolve tolerance via Numeric Policy SSOT if not provided
    if tol is None:
        tol = DEFAULT_TOLERANCES[MetricClass.TIME].abs

    prices = curve.prices
    pl = curve.pl

    be_points: List[float] = []
    for i in range(len(prices) - 1):
        y1, y2 = pl[i], pl[i + 1]
        if abs(y1) < tol:
            be_points.append(float(prices[i]))
        # שינוי סימן בין y1 ל־y2
        if y1 * y2 < 0:
            x1, x2 = prices[i], prices[i + 1]
            # אינטרפולציה ליניארית
            t = -y1 / (y2 - y1)
            be = x1 + t * (x2 - x1)
            be_points.append(float(be))

    be_points_sorted = sorted(set(round(x, 4) for x in be_points))
    return be_points_sorted


def summarize_position_pl(
    position: Position,
    center_price: float,
    lower_factor: float = 0.8,
    upper_factor: float = 1.2,
    num_points: int = 201,
) -> Dict[str, object]:
    """
    פונקציית "אול-אין-ואן" – לוקחת פוזיציה ומחזירה:
    - curve_df (DataFrame)
    - max_profit
    - max_loss
    - break_even_points
    כדי שיהיה נוח במסכים קיימים לקרוא פעם אחת ולקבל הכל.
    """
    prices = generate_price_range(
        center_price=center_price,
        lower_factor=lower_factor,
        upper_factor=upper_factor,
        num_points=num_points,
    )
    curve = generate_payoff_curve(position, prices)
    max_profit = calc_max_profit(curve)
    max_loss = calc_max_loss(curve)
    be_points = calc_break_even_points(curve)

    return {
        "curve_df": curve.to_dataframe(),
        "max_profit": max_profit,
        "max_loss": max_loss,
        "break_even_points": be_points,
    }
