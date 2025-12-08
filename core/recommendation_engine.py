# Layer: engine
# core/recommendation_engine.py
from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from core.scoring import score_strategy

# ... כאן כבר קיימת score_strategy(...)


class StrategyExplanation(TypedDict):
    score: float
    fit_label: str
    short_comment: str
    bullets: List[str]


def explain_strategy_score(
    goals: Dict[str, Any],
    summary: Dict[str, Any],
    *,
    score: float | None = None,
) -> StrategyExplanation:
    """
    מייצרת הסבר טקסטואלי קצר למה האסטרטגיה התאימה (או לא התאימה) לפרופיל.
    משתמשת בנתונים פשוטים: רווח/הפסד מקסימלי, הון מושקע (אם קיים), DTE וכו'.
    """

    # אם לא קיבלנו ציון – נחשב לפי הפונקציה הקיימת
    if score is None:
        score = float(score_strategy(goals, summary))
    else:
        score = float(score)

    bullets: List[str] = []

    # --- תיוג מילולי לציון ---
    if score >= 80:
        fit_label = "התאמה גבוהה"
    elif score >= 60:
        fit_label = "התאמה בינונית"
    else:
        fit_label = "התאמה נמוכה"

    # --- ניסיון לחשב אחוזי רווח/הפסד מההון אם יש הון מושקע ---
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

    # --- יעד רווח ---
    target_profit_pct = goals.get("target_profit_pct")
    if target_profit_pct is not None and max_profit_pct is not None:
        if max_profit_pct >= target_profit_pct:
            bullets.append(
                f"הרווח המקסימלי ({max_profit_pct:.1f}%) עומד ביעד הרווח שהגדרת ({target_profit_pct:.1f}%)."
            )
        else:
            bullets.append(
                f"הרווח המקסימלי ({max_profit_pct:.1f}%) נמוך מיעד הרווח שהגדרת ({target_profit_pct:.1f}%)."
            )

    # --- הפסד מקסימלי ---
    max_loss_goal = goals.get("max_loss_pct")
    if max_loss_goal is not None and max_loss_pct is not None:
        if max_loss_pct <= max_loss_goal:
            bullets.append(
                f"ההפסד המקסימלי ({max_loss_pct:.1f}%) נמצא בתוך גבול הסיכון שהגדרת ({max_loss_goal:.1f}%)."
            )
        else:
            bullets.append(
                f"ההפסד המקסימלי ({max_loss_pct:.1f}%) גבוה מהגבול שהגדרת ({max_loss_goal:.1f}%), ולכן הציון נמוך יותר."
            )

    # --- התאמת טווח זמן (DTE) ---
    dte_goal = goals.get("dte")
    dte_summary = summary.get("dte")  # אם אי פעם נוסיף את זה ל-summary
    if isinstance(dte_goal, (int, float)) and isinstance(dte_summary, (int, float)):
        diff = dte_summary - dte_goal
        if abs(diff) <= 7:
            bullets.append("טווח הזמן לפקיעה קרוב ליעד שביקשת.")
        elif diff > 7:
            bullets.append("האסטרטגיה בנויה לטווח זמן ארוך יותר מהיעד שביקשת.")
        else:
            bullets.append("האסטרטגיה בנויה לטווח זמן קצר יותר מהיעד שביקשת.")

    # --- אגרסיביות כללית לפי score ---
    aggressiveness = goals.get("aggressiveness")
    if aggressiveness is not None:
        if score >= 80:
            bullets.append("רמת הסיכון/תשואה מתאימה לרמת האגרסיביות שביקשת.")
        elif score <= 40:
            bullets.append(
                "קיימת סטייה מסוימת בין רמת האגרסיביות שביקשת לבין פרופיל האסטרטגיה."
            )

    # ניסוח קצר מחובר למשפט אחד-שניים
    if bullets:
        short_comment = " ".join(bullets[:2])
    else:
        short_comment = (
            "האסטרטגיה מתיישבת באופן כללי עם הפרופיל שהגדרת, לפי חישובי ה-MVP."
        )

    return StrategyExplanation(
        score=score,
        fit_label=fit_label,
        short_comment=short_comment,
        bullets=bullets,
    )
