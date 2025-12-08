# Layer: engine
# core/risk_engine.py
from __future__ import annotations
from typing import Any, Tuple


def classify_risk_level(
    max_loss: float,
    invested_capital: float,
    pos_greeks: Any,
) -> Tuple[str, str]:
    """
    מחזירה רמת סיכון כללית לפוזיציה:
    level: 'low' / 'medium' / 'high'
    comment: טקסט הסבר קצר למשתמש.
    """

    # אם אין הון מושקע – לא נוכל לחשב אחוזים בצורה חכמה
    if invested_capital <= 0:
        return (
            "medium",
            "לא הוגדר הון מושקע לפוזיציה – ההערכה איכותית בלבד (ללא חישוב אחוזי הפסד).",
        )

    loss_pct = abs(max_loss) / invested_capital * 100.0

    # נניח שהאובייקט של ה-Greeks כולל את השדות האלו (כמו שמחזירה calc_position_greeks)
    delta_abs = float(getattr(pos_greeks, "delta", 0.0))
    gamma_abs = float(getattr(pos_greeks, "gamma", 0.0))
    vega_abs = float(getattr(pos_greeks, "vega", 0.0))

    # ספים ראשוניים – נלטש אותם בעתיד לפי ניסיון / Backtesting
    # -------------------------------------------------------
    # loss_pct – כמה אחוז מההון אפשר להפסיד בתרחיש גרוע
    # delta_abs – חשיפה לכיוון (trend)
    # gamma_abs – רגישות לשינוי בדלתא (תנודתיות סביב הספוט)
    # vega_abs – רגישות לשינוי ב-IV

    if loss_pct <= 3 and delta_abs <= 10 and gamma_abs <= 0.0005 and vega_abs <= 50:
        level = "low"
        comment = (
            "רמת סיכון נמוכה: הפסד מקסימלי קטן ביחס להון שהוקצה, וחשיפת Greeks מתונה."
        )
    elif loss_pct <= 8 and delta_abs <= 25:
        level = "medium"
        comment = "רמת סיכון בינונית: הפסד אפשרי מורגש אך סביר, עם חשיפה כיוונית ותנודתית מוגבלת."
    else:
        level = "high"
        comment = "רמת סיכון גבוהה: הפסד מקסימלי משמעותי או חשיפת Greeks חדה (Delta / Gamma / Vega)."

    return level, comment
