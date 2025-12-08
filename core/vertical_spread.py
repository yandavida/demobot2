# Layer: strategies
# core/vertical_spread.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px


LegType = Literal["CALL", "PUT"]


@dataclass
class VerticalSpreadConfig:
    """קונפיגורציה בסיסית ל-Vertical Spread אחד."""

    short_strike: float
    long_strike: float
    cp: LegType  # "CALL" או "PUT"
    qty: int = 1
    multiplier: int = 100


def _build_vs_sidebar(df_view: pd.DataFrame) -> VerticalSpreadConfig:
    """
    בונה את ה־UI הקטן בתוך אזור האסטרטגיה (לא בסיידבר הראשי)
    ומחזיר VerticalSpreadConfig.
    """
    st.markdown("#### Vertical Spread parameters")

    strikes = sorted(df_view["strike"].unique().tolist())

    if len(strikes) < 2:
        st.warning("נדרשים לפחות שני סטרייקים כדי לבנות Vertical Spread.")
        # מחזירים ערכים דיפולטיביים כדי לא להפיל את הזרימה
        return VerticalSpreadConfig(
            short_strike=strikes[0] if strikes else 0.0,
            long_strike=strikes[0] if strikes else 0.0,
            cp="CALL",
            qty=1,
            multiplier=100,
        )

    col_type, col_short, col_long = st.columns(3)

    with col_type:
        cp = st.radio(
            "Type",
            ["CALL", "PUT"],
            horizontal=True,
            key="vs_cp",
        )

    mid_idx = len(strikes) // 2
    with col_short:
        short_strike = st.selectbox(
            "Short leg strike",
            strikes,
            index=mid_idx,
            key="vs_short",
        )
    with col_long:
        long_strike = st.selectbox(
            "Long leg strike",
            strikes,
            index=min(mid_idx + 1, len(strikes) - 1),
            key="vs_long",
        )

    col_qty, col_mult = st.columns(2)
    with col_qty:
        qty = st.number_input(
            "Contracts quantity",
            min_value=1,
            value=1,
            step=1,
            key="vs_qty",
        )
    with col_mult:
        multiplier = st.number_input(
            "Contract multiplier",
            min_value=1,
            value=100,
            step=1,
            key="vs_mult",
        )

    return VerticalSpreadConfig(
        short_strike=float(short_strike),
        long_strike=float(long_strike),
        cp=cp,  # "CALL"/"PUT"
        qty=int(qty),
        multiplier=int(multiplier),
    )


def _compute_vertical_payoff(
    cfg: VerticalSpreadConfig, df_view: pd.DataFrame
) -> tuple[dict, pd.DataFrame]:
    """
    מחשב מטריקות ו־payoff גרפי עבור Vertical Spread פשוט.
    כאן אנחנו *לא* משתמשים במחירי פרמיה – רק מבנה רגליים.
    """

    # טווח S לגרף – סביב טווח הסטרייקים ב־df_view
    all_strikes = df_view["strike"].values
    s_min = float(all_strikes.min()) * 0.9
    s_max = float(all_strikes.max()) * 1.1
    S = np.linspace(s_min, s_max, 300)

    # payoff ליחידה אחת (per 1 underlying)
    if cfg.cp == "CALL":
        # long call ב-long_strike, short call ב-short_strike
        payoff_unit = np.maximum(S - cfg.long_strike, 0.0) - np.maximum(
            S - cfg.short_strike, 0.0
        )
    else:  # PUT
        # long put ב-long_strike, short put ב-short_strike
        payoff_unit = np.maximum(cfg.long_strike - S, 0.0) - np.maximum(
            cfg.short_strike - S, 0.0
        )

    # סקיילינג לפי כמות ומכפיל
    pl = payoff_unit * cfg.multiplier * cfg.qty

    df_pay = pd.DataFrame({"S": S, "P/L": pl})

    # מטריקות פשוטות (ללא פרמיה – הנחה של net_credit = 0)
    wing = abs(cfg.long_strike - cfg.short_strike)
    max_profit = wing * cfg.multiplier * cfg.qty
    max_loss = -max_profit
    net_credit = 0.0

    # Break-even משוער (אמצע בין הסטרייקים – בדוגמה ללא פרמיה)
    be = (cfg.long_strike + cfg.short_strike) / 2.0

    metrics = {
        "net_credit": net_credit,
        "max_profit": max_profit,
        "max_loss": max_loss,
        "wing": wing,
        "break_even": be,
    }

    return metrics, df_pay


def render_vertical_spread(df_view: pd.DataFrame) -> None:
    """
    פונקציה שמתאימה ל־StrategyDefinition.render(df_view):
    מציירת את כל ה־UI של Vertical Spread על בסיס df_view.
    """

    st.markdown("### Vertical Spread (basic)")

    if df_view is None or len(df_view) == 0:
        st.warning("אין נתונים ב-df_view. צריך לייצר שרשרת ולעבור את הפילטרים.")
        return

    if "strike" not in df_view.columns:
        st.error("df_view לא מכיל עמודת 'strike' – אי אפשר לבנות Vertical Spread.")
        return

    cfg = _build_vs_sidebar(df_view)

    if cfg.short_strike == cfg.long_strike:
        st.error("הסטרייקים של הרגל הארוכה והקצרה חייבים להיות שונים.")
        return

    metrics, df_pay = _compute_vertical_payoff(cfg, df_view)

    # --- הצגת מטריקות ---
    st.markdown("#### Results")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Wing width", f"{metrics['wing']:.2f}")
    c2.metric("Max profit", f"{metrics['max_profit']:.0f}")
    c3.metric("Max loss", f"{metrics['max_loss']:.0f}")
    c4.metric("Net credit (approx.)", f"{metrics['net_credit']:.2f}")

    st.caption(f"Estimated break-even (mid): {metrics['break_even']:.2f}")

    # --- גרף payoff ---
    st.markdown("#### Payoff at expiry")

    fig = px.line(df_pay, x="S", y="P/L", title="Vertical Spread payoff (expiry)")
    fig.add_hline(y=0)
    st.plotly_chart(fig, use_container_width=True)
