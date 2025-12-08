# core/strategy_detector.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import pandas as pd

from core.models import Leg, Position


@dataclass(frozen=True)
class StrategyInfo:
    """
    מידע על אסטרטגיה מזוהה.

    name      – שם קצר (Iron Condor, Vertical Call Spread, Strangle...)
    subtype   – פירוט תת-סוג (Credit / Debit / Bullish / Bearish / Broken Wing...)
    description – הסבר מילולי קצר
    family    – משפחת אסטרטגיה (Income, Directional, Volatility, Hedging)
    risk_profile – תיאור מילולי של פרופיל הסיכון
    tags      – תגיות עיקריות (Theta+, Vega-, Neutral וכו')
    confidence – ציון ביטחון בין 0 ל-1
    """

    name: str
    subtype: Optional[str] = None
    description: str = ""
    family: Optional[str] = None
    risk_profile: Optional[str] = None
    tags: tuple[str, ...] = ()
    confidence: float = 1.0


# ============================================================
#   Utilities
# ============================================================


def _legs_by_type(position: Position) -> dict[str, list[Leg]]:
    calls = [leg for leg in position.legs if leg.cp == "CALL"]
    puts = [leg for leg in position.legs if leg.cp == "PUT"]
    return {"CALL": calls, "PUT": puts}


def _signed_quantity(leg: Leg) -> int:
    return leg.quantity if leg.side == "long" else -leg.quantity


def _is_vertical_spread(legs: list[Leg]) -> bool:
    """
    Vertical בסיסי:
    - שתי רגליים
    - אותו סוג (CALL/PUT)
    - סטרייקים שונים
    - צד הפוך
    """
    if len(legs) != 2:
        return False

    l1, l2 = legs
    if l1.cp != l2.cp:
        return False
    if l1.side == l2.side:
        return False
    if l1.strike == l2.strike:
        return False
    return True


def _vertical_info(legs: list[Leg]) -> tuple[bool, bool]:
    """
    מחזיר (is_credit, is_bullish) ל-Vertical Spread.
    חישוב קרדיט/דביט לפי פרמיות.
    ל-Call: שורי אם Long ב-strike נמוך יותר.
    ל-Put: שורי אם Short ב-strike גבוה יותר (Credit Put Spread).
    """
    l1, l2 = legs

    # מוודאים סדר: strike1 < strike2
    if l1.strike <= l2.strike:
        low, high = l1, l2
    else:
        low, high = l2, l1

    # נטו פרמיות (פר יחידה)
    pnl_low = _signed_quantity(low) * low.premium
    pnl_high = _signed_quantity(high) * high.premium
    net_credit = pnl_low + pnl_high
    is_credit = net_credit > 0

    if low.cp == "CALL":
        # שורי אם בלואו אנחנו לונג (Long Call Spread) או Short קרדיט מתחת?
        # תכל'ס: Vertical CALL:
        # Long low / Short high -> שורי דביט
        # Short low / Long high -> דובי קרדיט
        is_bullish = low.side == "long"
    else:
        # Vertical PUT:
        # Long high / Short low -> דובי דביט
        # Short high / Long low -> שורי קרדיט
        is_bullish = high.side == "short"

    return is_credit, is_bullish


def _is_iron_condor_like(calls: list[Leg], puts: list[Leg]) -> bool:
    """
    זיהוי Iron Condor בסיסי:
    - 2 CALL + 2 PUT
    - בכל צד: ספרד (long+short) עם סטרייקים שונים
    - כמויות מאוזנות (באופן גס)
    """
    if len(calls) != 2 or len(puts) != 2:
        return False

    calls_sorted = sorted(calls, key=lambda leg: leg.strike)
    puts_sorted = sorted(puts, key=lambda leg: leg.strike)

    c_strikes = [leg.strike for leg in calls_sorted]
    p_strikes = [leg.strike for leg in puts_sorted]

    if len(set(c_strikes)) != 2 or len(set(p_strikes)) != 2:
        return False

    # צדדים הפוכים בכל spread
    def _has_opposite_sides(legs_side: list[Leg]) -> bool:
        sides = {leg.side for leg in legs_side}
        return "long" in sides and "short" in sides

    if not _has_opposite_sides(calls_sorted):
        return False
    if not _has_opposite_sides(puts_sorted):
        return False

    # סדר סטרייקים תקין: put_low < put_high < call_low < call_high
    put_low, put_high = p_strikes
    call_low, call_high = c_strikes
    if not (put_low < put_high < call_low < call_high):
        return False

    return True


def _iron_condor_credit_or_debit(position: Position) -> tuple[bool, float]:
    """
    בודק האם הקונדור הוא קרדיט או דביט ומה גודל הקרדיט/דביט נטו (פר יחידה).
    חיובי = קרדיט, שלילי = דביט.
    """
    net = 0.0
    for leg in position.legs:
        sign = 1 if leg.side == "short" else -1
        net += sign * leg.premium * leg.quantity
    return (net > 0, net)


def _is_straddle(position: Position) -> bool:
    """
    Straddle:
    - שתי רגליים
    - CALL + PUT
    - אותו סטרייק
    - אותה כמות
    - אותו צד (Long/Short שניהם)
    """
    if len(position.legs) != 2:
        return False

    l1, l2 = position.legs
    if {l1.cp, l2.cp} != {"CALL", "PUT"}:
        return False
    if l1.strike != l2.strike:
        return False
    if l1.side != l2.side:
        return False
    if l1.quantity != l2.quantity:
        return False
    return True


def _is_strangle(position: Position) -> bool:
    """
    Strangle:
    - שתי רגליים
    - CALL + PUT
    - סטרייקים שונים
    - אותה כמות
    - אותו צד (Long/Short שניהם)
    """
    if len(position.legs) != 2:
        return False

    l1, l2 = position.legs
    if {l1.cp, l2.cp} != {"CALL", "PUT"}:
        return False
    if l1.side != l2.side:
        return False
    if l1.quantity != l2.quantity:
        return False
    if l1.strike == l2.strike:
        return False
    return True


def _is_ratio_spread(position: Position) -> bool:
    """
    Ratio Spread בסיסי:
    - כל הרגליים מאותו סוג (CALL או PUT)
    - לפחות 2 רגליים
    - יחס כמויות לא 1:1
    """
    if len(position.legs) < 2:
        return False

    cps = {leg.cp for leg in position.legs}
    if len(cps) != 1:
        return False

    total_long = sum(leg.quantity for leg in position.legs if leg.side == "long")
    total_short = sum(leg.quantity for leg in position.legs if leg.side == "short")
    if total_long == 0 or total_short == 0:
        return False

    # אם יש יחס לא 1:1 – נניח Ratio
    return total_long != total_short


# ============================================================
#   Main detection
# ============================================================


def detect_strategy(
    position: Position,
    spot: float | None = None,
    curve_df: Optional[pd.DataFrame] = None,
    be_points: Optional[Sequence[float]] = None,
) -> StrategyInfo:
    """
    זיהוי אסטרטגיה מתוך רשימת הרגליים.
    בנוי כך שיתאים גם לשימושים פשוטים (קריאה עם position בלבד)
    וגם לשימושים מתקדמים (כולל spot / payoff / BE).
    """

    # --- ללא רגליים ---
    if not position.legs:
        return StrategyInfo(
            name="No position",
            description="לא זוהתה אף רגל תקינה בפוזיציה.",
            family=None,
            risk_profile=None,
            tags=(),
            confidence=1.0,
        )

    legs = position.legs
    n_legs = len(legs)
    calls_puts = _legs_by_type(position)
    calls = calls_puts["CALL"]
    puts = calls_puts["PUT"]

    # --- מקרה של רגל בודדת ---
    if n_legs == 1:
        leg = legs[0]
        base_name = f"Single {leg.cp.title()}"
        subtype = "Long" if leg.side == "long" else "Short"
        family = "Directional" if leg.side == "long" else "Income / Hedging"
        desc = (
            f"רגל יחידה מסוג {leg.cp} בצד {leg.side}. "
            "פוזיציה לינארית יחסית עם Greeks ברורים ופשוטים."
        )
        tags: list[str] = []
        tags.append("Delta+" if leg.side == "long" and leg.cp == "CALL" else "")
        # לא צריך להתייפייף – מספיק להגיד Single Call / Put.
        return StrategyInfo(
            name=base_name,
            subtype=subtype,
            description=desc,
            family=family,
            risk_profile="סיכון פתוח בצד אחד של השוק.",
            tags=tuple(t for t in tags if t),
            confidence=0.95,
        )

    # --- Vertical Spread (2 רגליים, אותו סוג) ---
    if _is_vertical_spread(legs):
        is_credit, is_bullish = _vertical_info(legs)
        cp = legs[0].cp
        direction = "Bullish" if is_bullish else "Bearish"
        subtype_parts = [direction, "Credit" if is_credit else "Debit", cp.title()]
        subtype = " ".join(subtype_parts)

        if is_credit:
            family = "Income"
            risk_profile = "סיכון מוגבל, רווח מוגבל, קרדיט התחלתי."
        else:
            family = "Directional"
            risk_profile = "סיכון מוגבל, רווח מוגבל, דביט התחלתי."

        desc = (
            f"Vertical {cp.title()} Spread עם שתי רגליים בסטרייקים שונים וצד הפוך. "
            f"פרופיל {direction} עם סיכון ורווח מוגבלים."
        )

        tags: list[str] = [f"{cp.title()} Spread", direction]
        if is_credit:
            tags.append("Theta+")
        else:
            tags.append("Theta-")

        return StrategyInfo(
            name=f"Vertical {cp.title()} Spread",
            subtype=subtype,
            description=desc,
            family=family,
            risk_profile=risk_profile,
            tags=tuple(tags),
            confidence=0.98,
        )

    # --- Iron Condor (4 legs: 2 CALL + 2 PUT) ---
    if n_legs == 4 and _is_iron_condor_like(calls, puts):
        is_credit, net_credit = _iron_condor_credit_or_debit(position)

        # זיהוי Iron Fly אם שני השורטים באותו סטרייק (בערך המרכז)
        short_legs = [leg for leg in legs if leg.side == "short"]
        short_strikes = sorted({leg.strike for leg in short_legs})
        if len(short_strikes) == 1:
            name = "Iron Butterfly"
            base_desc = "Iron Butterfly (Iron Fly) – שיא רווח צר סביב סטרייק מרכזי."
        else:
            name = "Iron Condor"
            base_desc = "איירון קונדור סימטרי עם 4 רגליים (2 CALL + 2 PUT)."

        subtype_parts: list[str] = []
        if is_credit:
            subtype_parts.append("Credit")
        else:
            subtype_parts.append("Debit")

        subtype = " ".join(subtype_parts) if subtype_parts else None

        family = "Income"
        risk_profile = (
            "רווח מקסימלי מוגבל באזור האמצע, הפסד מקסימלי מוגבל בכנפיים. "
            "מתאים לשוק נייטרלי יחסית עם סטייה גבוהה יחסית (לקרדיט)."
        )

        desc = base_desc
        if is_credit:
            desc += " נפתחת כעסקת קרדיט – מקבלת פרמיה בתחילת הדרך."

        tags = ["Range-bound", "Theta+", "Vega-"]
        if is_credit:
            tags.append("Credit")

        confidence = 0.95

        return StrategyInfo(
            name=name,
            subtype=subtype,
            description=desc,
            family=family,
            risk_profile=risk_profile,
            tags=tuple(tags),
            confidence=confidence,
        )

    # --- Straddle / Strangle ---
    if _is_straddle(position):
        leg = position.legs[0]
        direction = "Long" if leg.side == "long" else "Short"
        name = f"{direction} Straddle"
        family = "Volatility"
        if direction == "Long":
            risk_profile = (
                "רווח פוטנציאלי גבוה בתנועה חדה מעלה/מטה, הפסד מוגבל לפרמיה הכוללת."
            )
            tags = ("Long Vol", "Gamma+", "Vega+", "Theta-")
        else:
            risk_profile = (
                "קבלת פרמיה גבוהה אך סיכון תאורטי גדול בתנועות חדות. "
                "אסטרטגיית כתיבה אגרסיבית."
            )
            tags = ("Short Vol", "Gamma-", "Vega-", "Theta+")

        return StrategyInfo(
            name=name,
            subtype=None,
            description="קנייה/מכירה סימולטנית של CALL ו-PUT באותו סטרייק.",
            family=family,
            risk_profile=risk_profile,
            tags=tags,
            confidence=0.96,
        )

    if _is_strangle(position):
        leg = position.legs[0]
        direction = "Long" if leg.side == "long" else "Short"
        name = f"{direction} Strangle"
        family = "Volatility"
        if direction == "Long":
            risk_profile = (
                "רווח פוטנציאלי גבוה בתנועות חדות, עם פרמיה זולה יותר מ-Straddle. "
                "דורש תנועה גדולה יותר כדי לעבור לרווח."
            )
            tags = ("Long Vol", "Gamma+", "Vega+", "Theta-")
        else:
            risk_profile = (
                "איסוף קרדיט משני הצדדים, אך חשיפה גבוהה לתנועות חדות. "
                "נחשב לכתיבה אגרסיבית למדי."
            )
            tags = ("Short Vol", "Gamma-", "Vega-", "Theta+")

        return StrategyInfo(
            name=name,
            subtype=None,
            description="קנייה/מכירה של CALL ו-PUT בסטרייקים שונים משני צידי המחיר.",
            family=family,
            risk_profile=risk_profile,
            tags=tags,
            confidence=0.94,
        )

    # --- Ratio Spread בסיסי ---
    if _is_ratio_spread(position):
        cp = position.legs[0].cp
        name = f"Ratio {cp.title()} Spread"
        family = "Directional / Volatility"
        risk_profile = (
            "אסטרטגיית Ratio – כמויות לא סימטריות של לונג/שורט באותו סוג אופציה. "
            "יכולה ליצור רווח בלתי מוגבל בצד אחד וסיכון מוגבל/לא מוגבל בצד אחר."
        )
        desc = (
            "קבוצת רגליים מאותו סוג (CALL/PUT) עם יחס כמויות שונה מ-1:1. "
            "משמשת ללקיחת כיוון עם פרופיל מורכב יותר."
        )
        return StrategyInfo(
            name=name,
            subtype=None,
            description=desc,
            family=family,
            risk_profile=risk_profile,
            tags=("Advanced", "Non-symmetric"),
            confidence=0.75,
        )

    # --- fallback: פוזיציה מורכבת שלא זוהתה ---
    return StrategyInfo(
        name="Custom / Complex Position",
        subtype=None,
        description=(
            "הפוזיציה מורכבת או אינה מתאימה לתבנית סטנדרטית אחת. "
            "ניתן לנתח אותה לפי גרף ה-P/L וה-Greeks."
        ),
        family="Custom",
        risk_profile=(
            "מומלץ לבחון את גרף הרווח/הפסד וה-Greeks כדי להבין "
            "את פרופיל הסיכון והרגישות לשוק."
        ),
        tags=("Complex",),
        confidence=0.5,
    )
