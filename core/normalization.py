# core/normalization.py
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional


# ==========================================
# Helpers כלליים
# ==========================================


def _as_float(value: Any, default: float | None = None) -> float | None:
    """ניסיון עדין להמיר ל-float, בלי לזרוק שגיאה."""
    if value is None:
        return default
    try:
        return float(value)
    except Exception:
        return default


def _as_int(value: Any, default: int | None = None) -> int | None:
    """ניסיון עדין להמיר ל-int, בלי לזרוק שגיאה."""
    if value is None:
        return default
    try:
        return int(value)
    except Exception:
        return default


# ==========================================
# Normalization ל-legs / position
# ==========================================


def normalize_position_legs(
    legs: List[Dict[str, Any]],
    *,
    default_multiplier: float = 1.0,
) -> List[Dict[str, Any]]:
    """
    מנרמל רשימת legs למבנה אחיד.
    מטרות:
    - side -> 'long' / 'short'
    - cp   -> 'CALL' / 'PUT'
    - strike, quantity, premium, multiplier -> טיפוסי מספר
    - expiry -> string (ISO) אם אפשר

    מחזיר רשימה חדשה (לא משנה את הקלט).
    """
    norm_legs: List[Dict[str, Any]] = []

    for leg in legs or []:
        side_raw = str(leg.get("side", "")).strip().lower()
        cp_raw = str(leg.get("cp", "")).strip().upper()

        if side_raw in ("buy", "long", "l"):
            side = "long"
        elif side_raw in ("sell", "short", "s"):
            side = "short"
        else:
            side = side_raw or "unknown"

        if cp_raw in ("C", "CALL"):
            cp = "CALL"
        elif cp_raw in ("P", "PUT"):
            cp = "PUT"
        else:
            cp = cp_raw or "UNKNOWN"

        strike = _as_float(leg.get("strike"), 0.0)
        quantity = _as_int(leg.get("quantity"), 0) or 0
        premium = _as_float(leg.get("premium"), 0.0)
        multiplier = (
            _as_float(leg.get("multiplier"), default_multiplier) or default_multiplier
        )

        expiry = leg.get("expiry")
        if expiry is None:
            expiry_str: Optional[str] = None
        else:
            expiry_str = str(expiry)

        norm_legs.append(
            {
                "side": side,
                "cp": cp,
                "strike": strike,
                "quantity": quantity,
                "premium": premium,
                "multiplier": multiplier,
                "expiry": expiry_str,
            }
        )

    return norm_legs


# ==========================================
# Normalization ל-Greeks
# ==========================================

GREEK_KEYS_DEFAULT = ("delta", "gamma", "vega", "theta", "rho")


def normalize_greeks(
    greeks: Dict[str, Any] | None,
    *,
    contract_multiplier: float | None = None,
    per_contract: bool = False,
    greek_keys: tuple[str, ...] = GREEK_KEYS_DEFAULT,
) -> Dict[str, Optional[float]]:
    """
    מנרמל מילון של Greeks:

    - ממיר כל ערך ל-float או None
    - אם contract_multiplier לא None:
        per_contract=False -> מכפיל לפי multiplier (ערך לפוזיציה)
        per_contract=True  -> מחלק לפי multiplier (ערך ליחידה)
    - מסנן את המפתחות לרשימת greek_keys (כמו delta, gamma וכו').

    מחזיר dict חדש עם ערכים נקיים.
    """
    if not greeks:
        return {k: None for k in greek_keys}

    norm: Dict[str, Optional[float]] = {}
    m = contract_multiplier or 1.0

    for key in greek_keys:
        raw_val = greeks.get(key)
        val = _as_float(raw_val, None)
        if val is None:
            norm[key] = None
            continue

        if m != 1.0:
            if per_contract:
                # הופך מערך לפוזיציה לערך ליחידה
                val = val / m
            else:
                # הופך מערך ליחידה לערך לפוזיציה
                val = val * m

        norm[key] = val

    return norm


# ==========================================
# Normalization ל-Payoff / P&L summary
# ==========================================


def normalize_payoff_summary(
    pl_summary: Dict[str, Any] | None,
) -> Dict[str, Optional[float]]:
    """
    מנרמל pl_summary למבנה אחיד:
    - pl_at_spot
    - max_profit
    - max_loss
    - notional_value
    מחזיר dict חדש, טיפוסים נורמליים.
    """
    if pl_summary is None:
        pl_summary = {}

    return {
        "pl_at_spot": _as_float(pl_summary.get("pl_at_spot"), 0.0),
        "max_profit": _as_float(pl_summary.get("max_profit"), None),
        "max_loss": _as_float(pl_summary.get("max_loss"), None),
        "notional_value": _as_float(
            pl_summary.get("notional_value") or pl_summary.get("notional_value_quote"),
            None,
        ),
    }


# ==========================================
# Normalization מלא לפלט של analyze_position
# ==========================================


def normalize_analysis_output(
    analysis: Dict[str, Any] | None,
    *,
    legs_raw: List[Dict[str, Any]] | None = None,
    contract_multiplier: float | None = None,
) -> Dict[str, Any]:
    """
    שכבת normalization לפלט של מנוע הניתוח (position/analyze).

    הקלט:
    - analysis: dict כמו שהמנוע מחזיר היום
    - legs_raw: רשימת legs מקורית (אופציונלי)
    - contract_multiplier: למקרה שרוצים לנרמל Greeks לפי מכפיל

    הפלט:
    - dict חדש, שלא משנה את המקור:
      {
        "legs": [... normalized ...],
        "pl_summary": {... normalized ...},
        "greeks": {... normalized ...},
        "break_even_points": [...],
        "curve": [...],
        "scenarios": [...],
        "risk_profile": {...},
        ...
      }
    """
    if analysis is None:
        analysis = {}

    result = deepcopy(analysis)

    # Legs
    if legs_raw is not None:
        result["legs"] = normalize_position_legs(legs_raw)
    elif "legs" in result:
        result["legs"] = normalize_position_legs(result.get("legs") or [])

    # P&L Summary
    result["pl_summary"] = normalize_payoff_summary(result.get("pl_summary"))

    # Greeks
    greeks_raw = result.get("greeks") or {}
    result["greeks"] = normalize_greeks(
        greeks_raw,
        contract_multiplier=contract_multiplier,
        per_contract=False,
    )

    # Break-even points – רשימה ממוינת של floats
    be_raw = result.get("break_even_points") or []
    be_list: List[float] = []
    for v in be_raw:
        f = _as_float(v, None)
        if f is not None:
            be_list.append(f)
    be_list = sorted(set(be_list))
    result["break_even_points"] = be_list

    # curve & scenarios – לא נוגעים במבנה, רק דואגים שלא יהיה None
    result["curve"] = result.get("curve") or []
    result["scenarios"] = result.get("scenarios") or []

    # risk_profile – אם חסר, מחזירים dict ריק
    result["risk_profile"] = result.get("risk_profile") or {}

    return result
