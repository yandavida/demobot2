# Layer: ui
# ui/controls.py

from typing import Sequence, Optional
import streamlit as st


def build_strategy_sidebar(
    strategies: Sequence,
    key_prefix: str = "strategy",
) -> Optional[object]:
    """
    מציג ב-sidebar בחירת אסטרטגיה מתוך רשימת StrategyDefinition
    (או אובייקטים עם name, label, render).

    מחזיר את ה־object שנבחר (לרוב StrategyDefinition),
    או None אם לא נבחרה אסטרטגיה.
    """

    if not strategies:
        st.sidebar.info("אין אסטרטגיות זמינות כרגע.")
        return None

    # שימוש ב-label להצגה, אבל שומרים mapping פנימי
    labels = ["None"] + [s.label for s in strategies]

    choice_label = st.sidebar.selectbox(
        "בחרי סטרטגיה לסימולטור",
        labels,
        index=1 if len(labels) > 1 else 0,
        key=f"{key_prefix}_strategy_choice",
    )

    if choice_label == "None":
        return None

    # מוצאים את האובייקט המתאים לפי label
    chosen = next((s for s in strategies if s.label == choice_label), None)
    return chosen
