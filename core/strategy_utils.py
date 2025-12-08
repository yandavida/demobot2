# core/strategy_utils.py
from __future__ import annotations

from typing import List

import pandas as pd

from core.models import Leg, Position
from core.payoff import payoff_position, summarize_position_pl
from core.greeks import calc_position_greeks
from core.strategy_warnings import get_position_warnings
from core.risk_engine import classify_risk_level
from core.scoring import score_strategy
from core.strategy_detector import detect_strategy


# ============================================================
#   פונקציות עזר לפוזיציות ואיירון קונדור
# ============================================================


def init_default_legs_df() -> pd.DataFrame:
    """טבלת רגליים ברירת מחדל – איירון קונדור לדוגמה."""
    data = [
        {"side": "short", "cp": "PUT", "strike": 4900.0, "quantity": 1, "premium": 4.0},
        {"side": "long", "cp": "PUT", "strike": 4800.0, "quantity": 1, "premium": 2.0},
        {
            "side": "short",
            "cp": "CALL",
            "strike": 5100.0,
            "quantity": 1,
            "premium": 4.2,
        },
        {"side": "long", "cp": "CALL", "strike": 5200.0, "quantity": 1, "premium": 2.1},
    ]
    return pd.DataFrame(data)


def df_to_position(df: pd.DataFrame) -> Position:
    """המרת DataFrame לפוזיציית Position עם סינון שגיאות רכות."""
    legs: List[Leg] = []

    for _, row in df.iterrows():
        try:
            side = str(row.get("side", "")).lower()
            cp_raw = str(row.get("cp", "")).upper()
            strike = float(row.get("strike"))
        except Exception:
            continue

        if side not in ("long", "short"):
            continue
        if cp_raw not in ("CALL", "PUT"):
            continue

        try:
            quantity = int(row.get("quantity", 1))
        except Exception:
            quantity = 1

        try:
            premium = float(row.get("premium", 0.0))
        except Exception:
            premium = 0.0

        legs.append(
            Leg(
                side=side,  # type: ignore[arg-type]
                cp=cp_raw,  # type: ignore[arg-type]
                strike=strike,
                quantity=quantity,
                premium=premium,
            )
        )

    return Position(legs=legs)


def compute_net_credit_per_unit(position: Position) -> float:
    """קרדיט/דביט נטו לפוזיציה (פר יחידה), ללא מכפיל חוזה."""
    net = 0.0
    for leg in position.legs:
        sign = 1 if leg.side == "short" else -1
        net += sign * leg.premium * leg.quantity
    return net


def analyze_payoff(position: Position, params: dict) -> dict:
    """
    חישוב עקומת P/L וסיכום כללי עבור פוזיציה אחת.
    מחזיר גם DataFrame של העקומה וגם Summary (כולל breakeven וכו').
    """
    curve_df = payoff_position(position, params)
    summary = summarize_position_pl(curve_df)
    return {
        "curve_df": curve_df,
        "summary": summary,
        "breakeven_points": summary.get("breakeven_points", []),
    }


def analyze_greeks(position: Position, params: dict) -> dict:
    """
    חישוב Greeks לפוזיציה.
    """
    try:
        greeks = calc_position_greeks(position, params)
    except Exception:
        greeks = {}
    return greeks


def analyze_risk(position: Position) -> dict:
    """
    מעטפת ל-classify_risk_level – אפשר להרחיב אחר כך לפי קונפיגורציה.
    כרגע מחזיר dict כללי של רמת סיכון.
    """
    try:
        risk = classify_risk_level(position)
    except Exception:
        risk = {}
    return risk


def analyze_warnings(position: Position) -> list[str]:
    """
    מעטפת ל-get_position_warnings – מחזירה רשימת אזהרות טקסטואליות.
    """
    try:
        warnings = get_position_warnings(position)
    except Exception:
        warnings = []
    return warnings


def analyze_scoring(position: Position) -> dict:
    """
    ניקוד אסטרטגיה + זיהוי אסטרטגיה.
    """
    try:
        detected = detect_strategy(position)
    except Exception:
        detected = None

    try:
        score = score_strategy(position)
    except Exception:
        score = {}

    return {
        "detected_strategy": detected,
        "score": score,
    }
