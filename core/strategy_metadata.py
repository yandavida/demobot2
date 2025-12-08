# Layer: strategies
# core/strategy_metadata.py
from __future__ import annotations

from typing import Any, Dict, List


def get_strategy_comparison_rows() -> List[Dict[str, Any]]:
    """
    מחזיר רשימת מילונים – כל מילון מייצג אסטרטגיה אחת לטבלת ההשוואה
    ולעמוד Strategy Overview.
    """

    rows: List[Dict[str, Any]] = []

    # 1) Iron Condor (Credit)
    rows.append(
        {
            "Strategy": "Iron Condor (Credit)",
            "Position type": "Credit",
            "Risk profile": "Defined risk, limited profit",
            "Volatility view": "Expect realized volatility to stay within a range",
            "Direction bias": "Market-neutral to slightly directional",
            "Legs": 4,
            "Risk level": 3,  # 1–5 (1 נמוך, 5 גבוה)
            "Complexity level": 4,  # 1–5 (1 פשוט, 5 מורכב)
            "Typical use (EN)": (
                "Sell premium when you expect the underlying to stay within a price "
                "range into expiry. Good for range-bound markets where IV is not too low."
            ),
            "מתאים לי כש…": (
                "אני מאמינה שהנכס יישאר בטווח מחירים מוגדר עד הפקיעה, ורוצה להכניס קרדיט "
                "עם סיכון מוגבל. מתאימה כשאני מבינה היטב את המרחק בין הסטרייקים ואת הסיכון "
                "במצבי קצה (פריצה חדה למעלה או למטה)."
            ),
        }
    )

    # 2) Bull Put Spread
    rows.append(
        {
            "Strategy": "Bull Put Spread",
            "Position type": "Credit",
            "Risk profile": "Defined risk, bullish",
            "Volatility view": "Prefer stable or slightly decreasing IV",
            "Direction bias": "Bullish",
            "Legs": 2,
            "Risk level": 3,  # הוגדל מ־2 → 3
            "Complexity level": 2,
            "Typical use (EN)": (
                "Collect premium while taking a defined-risk bullish view. You profit "
                "if the underlying stays above the short put strike (or doesn’t fall too much)."
            ),
            "מתאים לי כש…": (
                "אני חיובית על הנכס אבל רוצה סיכון מוגבל ולא רכישת קול יקרה. "
                "מתאים כשאני חושבת שהנכס יישאר מעל רמת מחיר מסוימת, "
                "וגם מוכנה להתמודד עם ירידה בינונית כל עוד היא מוגבלת."
            ),
        }
    )

    # 3) Bear Call Spread
    rows.append(
        {
            "Strategy": "Bear Call Spread",
            "Position type": "Credit",
            "Risk profile": "Defined risk, bearish",
            "Volatility view": "Prefer stable or slightly decreasing IV",
            "Direction bias": "Bearish",
            "Legs": 2,
            "Risk level": 3,  # הוגדל מ־2 → 3
            "Complexity level": 2,
            "Typical use (EN)": (
                "Take a defined-risk bearish view and collect premium. You profit "
                "if the underlying stays below the short call strike or does not rally too much."
            ),
            "מתאים לי כש…": (
                "אני סקפטית לגבי המשך עליות בנכס, ורוצה להרוויח מקרדיט כל עוד המחיר "
                "לא פורץ למעלה בצורה חדה. מתאים כשאני צופה דשדוש או ירידה קלה, "
                "ומבינה את הסיכון בסקויזים/ריצות חדות למעלה."
            ),
        }
    )

    # 4) Long Straddle
    rows.append(
        {
            "Strategy": "Long Straddle",
            "Position type": "Debit",
            "Risk profile": "High risk, unlimited profit potential",
            "Volatility view": "Expect large move and/or IV expansion",
            "Direction bias": "Direction-agnostic (long volatility)",
            "Legs": 2,
            "Risk level": 5,  # הוגדל מ־4 → 5
            "Complexity level": 4,  # הוגדל מ־3 → 4
            "Typical use (EN)": (
                "Buy both a call and a put at the same strike when you expect a big move "
                "but are unsure about direction (e.g., major events, earnings, macro data)."
            ),
            "מתאים לי כש…": (
                "אני מצפה לתנודה גדולה בנכס (למעלה או למטה) סביב אירוע משמעותי – "
                "אבל לא יודעת לאיזה כיוון. אני מבינה שתיתכן שחיקת ערך מהירה אם "
                "התנודה בפועל קטנה או שסטיית התקן מתכווצת אחרי האירוע."
            ),
        }
    )

    return rows
