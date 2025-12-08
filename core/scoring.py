# Layer: engine
# core/scoring.py
from __future__ import annotations
from typing import Mapping, Any, Sequence


def score_strategy(goals: Mapping[str, Any], summary: Mapping[str, Any]) -> float:
    """
    חישוב ציון לאסטרטגיה בהתאם לפרופיל היעדים.

    goals: dict עם מפתחות צפויים:
        - target_profit_pct
        - max_loss_pct
        - dte
        - aggressiveness
        - market_view
        - spot

    summary: dict שמוחזר מ-summarize_position_pl:
        - max_profit
        - max_loss
        - break_even_points
    """
    # --- קריאת פרופיל היעדים בצורה סלחנית ---
    try:
        target_profit_pct = float(goals.get("target_profit_pct", 0.0))
        aggressiveness = int(goals.get("aggressiveness", 5))
        spot = float(goals.get("spot", 1.0) or 1.0)
    except Exception:
        target_profit_pct = 0.0
        aggressiveness = 5
        spot = 1.0

    max_profit = float(summary.get("max_profit", 0.0) or 0.0)
    max_loss = float(summary.get("max_loss", 0.0) or 0.0)
    be_points: Sequence[float] = summary.get("break_even_points") or []

    score = 0.0

    # --- יחס סיכון/תשואה (R/R) בסיסי ---
    if max_loss < 0:
        if max_profit > 0:
            rr = max_profit / abs(max_loss)
        else:
            rr = 0.0
    else:
        rr = 0.0
        # ענישה על אסטרטגיות שבהן max_loss לא מוגדר היטב / לא מוגבל
        score -= 2.0

    # נותנים משקל ל-R/R
    score += 1.5 * rr

    # --- התאמה ליעד רווח באחוזים (בקירוב) ---
    # מניחים "תשואה משוערת" ~ R/R * 100 (לא מושלם, אבל מספיק להעדפה יחסית)
    roi_pct = rr * 100.0
    profit_gap = abs(roi_pct - target_profit_pct)
    profit_gap = min(profit_gap, 100.0)  # לא להעניש בלי סוף

    # ככל שהפער מהיעד גדול – מורידים מעט מהציון
    score -= 0.02 * profit_gap

    # --- רוחב טווח ה-BE והקשר לאגרסיביות ---
    # שמרני: יעדיף טווח BE רחב (יותר מרחב נשימה)
    # אגרסיבי: יעדיף טווח BE צר עם R/R גבוה
    if isinstance(be_points, Sequence) and len(be_points) >= 2 and spot > 0:
        width = float(max(be_points) - min(be_points))
        width_norm = width / spot  # כמה רחב הטווח יחסית למחיר

        if aggressiveness <= 3:
            # שמרני – בונוס לטווח BE רחב
            score += 0.5 * width_norm
        elif aggressiveness >= 7:
            # אגרסיבי – בונוס דווקא לטווח צר יותר
            score += 0.5 * max(0.0, 1.0 - min(width_norm, 2.0))

    return float(score)
