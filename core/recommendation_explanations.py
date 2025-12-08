# Layer: engine
# core/recommendation_explanations.py
from __future__ import annotations

from typing import Any, Dict, List, TypedDict


class StrategyExplanation(TypedDict):
    score: float
    fit_label: str
    short_comment: str
    bullets: List[str]


def build_explanation_for_strategy(
    goals: Dict[str, Any],
    summary: Dict[str, Any],
    *,
    score: float,
    risk_level: str | None = None,
    risk_comment: str | None = None,
) -> StrategyExplanation:
    """
    מייצרת הסבר טקסטואלי למה האסטרטגיה מתאימה (או לא מתאימה) לפרופיל.
    אין כאן חישובים חדשים – רק פירוק של מה שכבר קיים לשפה אנושית.
    """

    # --- תיוג מילולי לציון ---
    if score >= 80:
        fit_label = "התאמה גבוהה"
    elif score >= 60:
        fit_label = "התאמה בינונית"
    else:
        fit_label = "התאמה נמוכה"

    bullets: List[str] = []

    # --- נתונים בסיסיים מה-summary ---
    max_profit = float(summary.get("max_profit", 0.0))
    max_loss = float(summary.get("max_loss", 0.0))

    invested_capital = summary.get("invested_capital")
    if invested_capital is None:
        invested_capital = summary.get("capital_at_risk")
    invested_capital = float(invested_capital or 0.0)

    max_profit_pct = None
    max_loss_pct = None
    if invested_capital > 0:
        max_profit_pct = (max_profit / invested_capital) * 100.0
        max_loss_pct = (abs(max_loss) / invested_capital) * 100.0

    target_profit_pct = goals.get("target_profit_pct")
    max_loss_goal = goals.get("max_loss_pct")
    dte_goal = goals.get("dte")

    # --- Bullet: יחס רווח ליעד ---
    if target_profit_pct is not None and max_profit_pct is not None:
        if max_profit_pct >= target_profit_pct:
            bullets.append(
                f"הרווח המקסימלי הפוטנציאלי ({max_profit_pct:.1f}%) עומד ביעד הרווח שהגדרת ({target_profit_pct:.1f}%)."
            )
        else:
            bullets.append(
                f"הרווח המקסימלי ({max_profit_pct:.1f}%) נמוך מיעד הרווח שביקשת ({target_profit_pct:.1f}%), ולכן הציון מעט נמוך יותר."
            )

    # --- Bullet: סיכון מקסימלי ביחס לגבול שהוגדר ---
    if max_loss_goal is not None and max_loss_pct is not None:
        if max_loss_pct <= max_loss_goal:
            bullets.append(
                f"ההפסד המקסימלי ({max_loss_pct:.1f}%) נמצא בתוך גבול הסיכון שהגדרת ({max_loss_goal:.1f}%)."
            )
        else:
            bullets.append(
                f"ההפסד המקסימלי ({max_loss_pct:.1f}%) גבוה מגבול הסיכון שהגדרת ({max_loss_goal:.1f}%), ולכן האסטרטגיה נחשבת אגרסיבית יותר עבורך."
            )

    # --- Bullet: זמן לפקיעה (אם אי פעם נוסיף dte ל-summary) ---
    dte_summary = summary.get("dte")
    if isinstance(dte_goal, (int, float)) and isinstance(dte_summary, (int, float)):
        diff = dte_summary - dte_goal
        if abs(diff) <= 7:
            bullets.append("טווח הזמן לפקיעה קרוב ליעד שביקשת.")
        elif diff > 7:
            bullets.append("האסטרטגיה בנויה לטווח זמן ארוך יותר מהיעד שביקשת.")
        else:
            bullets.append("האסטרטגיה בנויה לטווח זמן קצר יותר מהיעד שביקשת.")

    # --- Bullet: רמת סיכון כללית לפי risk engine ---
    if risk_level:
        if risk_comment:
            bullets.append(risk_comment)
        else:
            bullets.append(
                f"רמת הסיכון הכוללת של הפוזיציה מסווגת כ־{risk_level} לפי גודל ההפסד המקסימלי וה-Greeks."
            )

    # --- Bullet: התאמה לאגרסיביות (מאקרו לפי score) ---
    aggressiveness = goals.get("aggressiveness")
    if aggressiveness is not None:
        if score >= 80:
            bullets.append(
                "רמת הסיכון/תשואה של האסטרטגיה מתיישבת היטב עם רמת האגרסיביות שביקשת."
            )
        elif score <= 40:
            bullets.append(
                "קיימת סטייה בין רמת האגרסיביות שהגדרת לבין פרופיל הסיכון של האסטרטגיה."
            )

    # ניסוח קצר למשפט אחד–שניים
    if bullets:
        short_comment = " ".join(bullets[:2])
    else:
        short_comment = (
            "האסטרטגיה מתיישבת באופן כללי עם הפרופיל שהגדרת, לפי חישובי ה-MVP."
        )

    return StrategyExplanation(
        score=float(score),
        fit_label=fit_label,
        short_comment=short_comment,
        bullets=bullets,
    )
