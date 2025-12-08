# Layer: ui
# ui/risk_components.py

import streamlit as st

RISK_LABELS = {
    "low": "נמוכה",
    "medium": "בינונית",
    "high": "גבוהה",
}

RISK_CLASS = {
    "low": "risk-chip risk-low",
    "medium": "risk-chip risk-medium",
    "high": "risk-chip risk-high",
}


def render_risk_chip(level: str, comment: str):
    label = RISK_LABELS.get(level, "בינונית")
    css_class = RISK_CLASS.get(level, "risk-chip risk-medium")

    st.markdown("### פרופיל סיכון כללי")
    st.markdown(
        f'<div class="{css_class}">רמת סיכון: {label}</div>',
        unsafe_allow_html=True,
    )
    st.caption(comment)
