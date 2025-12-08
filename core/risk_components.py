# ui/risk_components.py
from __future__ import annotations

import streamlit as st


def _inject_risk_css() -> None:
    """מזריק CSS קטן לצ'יפים של רמת סיכון (רק פעם אחת לסשן)."""
    if st.session_state.get("_risk_css_injected"):
        return

    st.session_state["_risk_css_injected"] = True
    st.markdown(
        """
        <style>
        .risk-chip {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 0.3rem;
        }
        .risk-low {
            background: rgba(22, 163, 74, 0.15);
            border: 1px solid #16a34a;
            color: #bbf7d0;
        }
        .risk-medium {
            background: rgba(234, 179, 8, 0.12);
            border: 1px solid #eab308;
            color: #fef9c3;
        }
        .risk-high {
            background: rgba(220, 38, 38, 0.15);
            border: 1px solid #ef4444;
            color: #fee2e2;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_risk_chip(level: str, comment: str) -> None:
    """מציג צ'יפ צבעוני + הערת טקסט לפי רמת הסיכון."""
    _inject_risk_css()

    label_map = {
        "low": "נמוכה",
        "medium": "בינונית",
        "high": "גבוהה",
    }

    css_class = {
        "low": "risk-chip risk-low",
        "medium": "risk-chip risk-medium",
        "high": "risk-chip risk-high",
    }.get(level, "risk-chip risk-medium")

    label = label_map.get(level, "בינונית")

    st.markdown("### פרופיל סיכון כללי")
    st.markdown(
        f'<div class="{css_class}">רמת סיכון: {label}</div>',
        unsafe_allow_html=True,
    )
    st.caption(comment)
