# core/validation.py
from __future__ import annotations

from typing import Dict, List, Any


def validate_greeks(greeks: Dict[str, Any]) -> List[str]:
    """
    בדיקות sanity על Greeks:
    - None / NaN / אינסוף / ערכים לא סבירים
    """
    warnings: List[str] = []
    if not greeks:
        return warnings

    for key, value in greeks.items():
        try:
            if value is None:
                warnings.append(f"{key} is None")
            elif isinstance(value, float) and (value != value):  # NaN
                warnings.append(f"{key} is NaN")
            elif isinstance(value, float) and abs(value) > 1e6:
                warnings.append(f"{key} is extremely large ({value})")
        except Exception:
            warnings.append(f"Invalid greek value for {key}")

    return warnings


def validate_break_even(be_points: List[float]) -> List[str]:
    """
    בדיקות על נקודות Break-even:
    - סדר
    - כפילויות
    """
    warnings: List[str] = []
    if not be_points:
        return warnings

    # חייב להיות ממוין לא יורד
    if any(be_points[i] > be_points[i + 1] for i in range(len(be_points) - 1)):
        warnings.append("Break-even points are not sorted")

    # כפילויות
    if len(set(be_points)) != len(be_points):
        warnings.append("Duplicate break-even points detected")

    return warnings


def validate_position_structure(legs: List[Dict[str, Any]]) -> List[str]:
    """
    בדיקות בסיס על מבנה הפוזיציה:
    - אין Legs
    - סכום כמויות = 0
    - side לא תקין
    """
    warnings: List[str] = []

    if not legs:
        warnings.append("No legs in position")
        return warnings

    total_qty = 0
    for leg in legs:
        try:
            total_qty += int(leg.get("quantity", 0))
        except Exception:
            warnings.append("Invalid quantity value in legs")

        side = str(leg.get("side", "")).lower()
        if side not in ("long", "short"):
            warnings.append(f"Invalid side in leg: {side}")

    if total_qty == 0:
        warnings.append(
            "Position net quantity sums to zero — may be reversed or invalid"
        )

    return warnings


def validate_analysis_output(analysis: Dict[str, Any]) -> List[str]:
    """
    פונקציה מרכזית שמקבלת dict של ניתוח פוזיציה
    ומחזירה רשימת אזהרות טקסטואליות.
    analysis צפוי לכלול:
    - greeks: dict
    - break_even_points: list[float]
    - pl_summary: dict עם pl_at_spot
    - legs_raw: list[dict] (נוסיף ב-router מה-request)
    """
    warnings: List[str] = []

    legs = analysis.get("legs_raw", [])
    warnings.extend(validate_position_structure(legs))

    greeks = analysis.get("greeks", {}) or {}
    warnings.extend(validate_greeks(greeks))

    be_points = analysis.get("break_even_points", []) or []
    warnings.extend(validate_break_even(be_points))

    # Sanity על P/L לפי Spot
    pl_summary = analysis.get("pl_summary", {}) or {}
    pl_at_spot = pl_summary.get("pl_at_spot", None)
    try:
        if isinstance(pl_at_spot, (int, float)) and abs(float(pl_at_spot)) > 1e9:
            warnings.append(f"P/L at spot is extremely large: {pl_at_spot}")
    except Exception:
        warnings.append("Invalid P/L at spot in pl_summary")

    return warnings
