# Layer: engine
# core/strategy_warnings.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from core.models import Position, Leg
from core.greeks import Greeks


@dataclass
class WarningConfig:
    """
    ספי אזהרות פשוטים. אם נרצה בעתיד – אפשר להוציא לקובץ קונפיג.
    """

    max_abs_delta: float = 200.0  # חשיפת דלתא מותרת (יח' נכס)
    max_abs_gamma: float = 1.0  # סף גמא "גבוהה"
    max_abs_vega: float = 200.0  # חשיפת וגא ל-1% שינוי IV
    max_abs_theta: float = 200.0  # שינוי יומי מקסימלי "סביר"
    close_be_threshold_pct: float = 2.0  # BE קרוב מ-2% ל-spot נחשב "צמוד"


def _find_uncovered_short_calls(legs: Iterable[Leg]) -> bool:
    """
    בודק האם קיימת רגל CALL שורט שלא מכוסה ע"י CALL לונג בסטרייק גבוה יותר.
    זה לא מושלם, אבל נותן אינדיקציה טובה לסיכון "נייקד קול".
    """
    short_calls = [leg for leg in legs if leg.cp == "CALL" and leg.side == "short"]
    long_calls = [leg for leg in legs if leg.cp == "CALL" and leg.side == "long"]

    if not short_calls:
        return False

    if not long_calls:
        # יש שורטים ואין בכלל לונגים – סיכון נייקד ברור
        return True

    for sc in short_calls:
        covered_qty = sum(lc.quantity for lc in long_calls if lc.strike >= sc.strike)
        if covered_qty < sc.quantity:
            return True

    return False


def _find_uncovered_short_puts(legs: Iterable[Leg]) -> bool:
    """
    בודק האם קיימת רגל PUT שורט שלא מכוסה ע"י PUT לונג בסטרייק נמוך יותר.
    (שוב – הערכה, לא חישוב מרג'ין מדויק).
    """
    short_puts = [leg for leg in legs if leg.cp == "PUT" and leg.side == "short"]
    long_puts = [leg for leg in legs if leg.cp == "PUT" and leg.side == "long"]

    if not short_puts:
        return False

    if not long_puts:
        return True

    for sp in short_puts:
        covered_qty = sum(lp.quantity for lp in long_puts if lp.strike <= sp.strike)
        if covered_qty < sp.quantity:
            return True

    return False


def _is_position_size_unbalanced(legs: Sequence[Leg]) -> bool:
    """
    מזהה חוסר סימטריה בכמויות בין לונגים לשורטים.
    לא אומר שזה "אסור", אבל שווה תשומת לב.
    """
    total_long = sum(leg.quantity for leg in legs if leg.side == "long")
    total_short = sum(leg.quantity for leg in legs if leg.side == "short")

    return total_long != total_short


def _closest_be_to_spot(spot: float, be_prices: Sequence[float]) -> float | None:
    if spot <= 0 or not be_prices:
        return None
    distances_pct = [abs(be - spot) / spot * 100.0 for be in be_prices]
    return min(distances_pct) if distances_pct else None


def get_position_warnings(
    position: Position,
    spot: float | None = None,
    greeks: Greeks | None = None,
    be_prices: Sequence[float] | None = None,
    config: WarningConfig | None = None,
) -> list[str]:
    """
    מחזירה רשימת אזהרות טקסטואליות לפוזיציה.
    כל אזהרה היא string בעברית, לשימוש ב־UI.
    """
    if config is None:
        config = WarningConfig()

    warnings: list[str] = []
    legs = position.legs

    if not legs:
        return warnings

    # --- אזהרות כמותיות בסיסיות ---
    if _is_position_size_unbalanced(legs):
        warnings.append(
            "כמויות הרגליים הלונג והשורט אינן מאוזנות. "
            "ייתכן שהפוזיציה אינה סימטרית או שמדובר באסטרטגיה אגרסיבית יותר."
        )

    # --- uncovered / naked ---
    if _find_uncovered_short_calls(legs):
        warnings.append(
            'זוהו CALL קצרות שאינן מכוסות באופן מלא ע"י CALL ארוכות בסטרייק גבוה יותר – '
            "ייתכן שקיימת חשיפת 'נייקד קול' עם סיכון תיאורטי לא מוגבל."
        )

    if _find_uncovered_short_puts(legs):
        warnings.append(
            'זוהו PUT קצרות שאינן מכוסות באופן מלא ע"י PUT ארוכות בסטרייק נמוך יותר – '
            "ייתכן שקיימת חשיפת 'נייקד פוט' עם סיכון משמעותי במקרה של ירידה חדה."
        )

    # --- Greeks-based diagnostics ---
    if greeks is not None:
        if abs(greeks.delta) > config.max_abs_delta:
            warnings.append(
                f"דלתא כוללת גבוהה (≈ {greeks.delta:,.0f} יח' נכס). "
                "הפוזיציה מתנהגת דומה לפוזיציית ספוט גדולה – רגישות גבוהה לתנועת מחיר."
            )

        if abs(greeks.gamma) > config.max_abs_gamma:
            warnings.append(
                f"גמא גבוהה (≈ {greeks.gamma:,.3f}). "
                "שימי לב: דלתא הפוזיציה עשויה להשתנות במהירות סביב המחיר הנוכחי."
            )

        if abs(greeks.vega) > config.max_abs_vega:
            warnings.append(
                f"חשיפת וגא גבוהה לסטייה (≈ {greeks.vega:,.0f} ל-1% שינוי ב-IV). "
                "הפוזיציה רגישה מאוד לשינויי סטיית תקן משתמעת."
            )

        if abs(greeks.theta) > config.max_abs_theta:
            warnings.append(
                f"חשיפת תטא יומית גבוהה (≈ {greeks.theta:,.0f} ליום). "
                "שימי לב לקצב השחיקה היומי ברווח/הפסד."
            )

    # --- Break-even proximity ---
    if spot is not None and be_prices:
        closest_be = _closest_be_to_spot(spot, be_prices)
        if closest_be is not None and closest_be < config.close_be_threshold_pct:
            warnings.append(
                f"נקודת איזון קרובה יחסית למחיר הנוכחי (~{closest_be:.1f}% בלבד). "
                "הפוזיציה עלולה לעבור מאזור רווח לאזור הפסד בתנועה קטנה יחסית."
            )

    return warnings
