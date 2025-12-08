# Layer: strategies
# core/short_butterfly.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px


LegType = Literal["CALL", "PUT"]


@dataclass
class ShortButterflyConfig:
    """קונפיגורציה בסיסית ל-Short Butterfly (הופכי ל-Long 1:-2:1)."""

    lower_strike: float
    middle_strike: float
    upper_strike: float
    cp: LegType  # "CALL" או "PUT"
    qty: int = 1
    multiplier: int = 100


def _find_mid_price(df_view: pd.DataFrame, strike: float, cp: LegType) -> float:
    """
    מחפש אופציה (CALL/PUT) ב-strike נתון ומחזיר mid-price.
    אם אין bid/ask – משתמש בעמודת price.
    """
    mask = (df_view["strike"] == strike) & (df_view["cp"].str.upper() == cp.upper())
    row = df_view.loc[mask].head(1)

    if row.empty:
        raise ValueError(f"לא נמצאה אופציה עבור strike={strike}, cp={cp}")

    if "bid" in row.columns and "ask" in row.columns:
        bid = float(row["bid"].iloc[0])
        ask = float(row["ask"].iloc[0])
        return 0.5 * (bid + ask)

    return float(row["price"].iloc[0])


def _build_short_butterfly_ui(df_view: pd.DataFrame) -> ShortButterflyConfig:
    """
    UI לבחירת סטרייקים וכמות עבור Short Butterfly.
    """
    st.markdown("#### Short Butterfly parameters")

    strikes = sorted(df_view["strike"].unique().tolist())

    if len(strikes) < 3:
        st.warning("נדרשים לפחות שלושה סטרייקים כדי לבנות Butterfly.")
        base = strikes[0] if strikes else 0.0
        return ShortButterflyConfig(
            lower_strike=base,
            middle_strike=base,
            upper_strike=base,
            cp="CALL",
            qty=1,
            multiplier=100,
        )

    col_type, col_l, col_m, col_u = st.columns(4)

    with col_type:
        cp = st.radio(
            "Type",
            ["CALL", "PUT"],
            horizontal=True,
            key="sbf_cp",
        )

    n = len(strikes)
    mid_idx = n // 2
    lower_default = max(0, mid_idx - 1)
    upper_default = min(n - 1, mid_idx + 1)

    with col_l:
        lower_strike = st.selectbox(
            "Lower strike (short)",
            strikes,
            index=lower_default,
            key="sbf_lower",
        )
    with col_m:
        middle_strike = st.selectbox(
            "Middle strike (long x2)",
            strikes,
            index=mid_idx,
            key="sbf_middle",
        )
    with col_u:
        upper_strike = st.selectbox(
            "Upper strike (short)",
            strikes,
            index=upper_default,
            key="sbf_upper",
        )

    col_qty, col_mult = st.columns(2)
    with col_qty:
        qty = st.number_input(
            "Contracts quantity",
            min_value=1,
            value=1,
            step=1,
            key="sbf_qty",
        )
    with col_mult:
        multiplier = st.number_input(
            "Contract multiplier",
            min_value=1,
            value=100,
            step=1,
            key="sbf_mult",
        )

    return ShortButterflyConfig(
        lower_strike=float(lower_strike),
        middle_strike=float(middle_strike),
        upper_strike=float(upper_strike),
        cp=cp,
        qty=int(qty),
        multiplier=int(multiplier),
    )


def _compute_short_butterfly_payoff(
    cfg: ShortButterflyConfig,
    df_view: pd.DataFrame,
) -> tuple[dict, pd.DataFrame]:
    """
    Short Butterfly: ההופכי של Long Butterfly (1:-2:1),
    כלומר: -1 lower, +2 middle, -1 upper (נטו קרדיט).
    """

    p_lower = _find_mid_price(df_view, cfg.lower_strike, cfg.cp)
    p_middle = _find_mid_price(df_view, cfg.middle_strike, cfg.cp)
    p_upper = _find_mid_price(df_view, cfg.upper_strike, cfg.cp)

    # קרדיט נטו ליחידה
    # short lower + short upper - 2 * long middle
    net_credit_per_unit = -p_lower - p_upper + 2.0 * p_middle
    total_credit = net_credit_per_unit * cfg.multiplier * cfg.qty

    # טווח מחירים S לגרף
    all_strikes = df_view["strike"].values
    s_min = float(all_strikes.min()) * 0.8
    s_max = float(all_strikes.max()) * 1.2
    S = np.linspace(s_min, s_max, 400)

    # payoff per 1 underlying:
    # ההופכי של long butterfly payoff
    if cfg.cp == "CALL":
        payoff_unit = (
            -np.maximum(S - cfg.lower_strike, 0.0)
            + 2.0 * np.maximum(S - cfg.middle_strike, 0.0)
            - np.maximum(S - cfg.upper_strike, 0.0)
            + net_credit_per_unit
        )
    else:  # PUT
        payoff_unit = (
            -np.maximum(cfg.lower_strike - S, 0.0)
            + 2.0 * np.maximum(cfg.middle_strike - S, 0.0)
            - np.maximum(cfg.upper_strike - S, 0.0)
            + net_credit_per_unit
        )

    pl = payoff_unit * cfg.multiplier * cfg.qty

    df_pay = pd.DataFrame({"S": S, "P/L": pl})

    wing_1 = abs(cfg.middle_strike - cfg.lower_strike)
    wing_2 = abs(cfg.upper_strike - cfg.middle_strike)
    wing_min = min(wing_1, wing_2)

    # בקירוב: max profit ≈ total_credit, max loss ≈ (wing_min - net_credit_per_unit) * multiplier * qty
    max_profit_approx = total_credit
    max_loss_approx = float(pl.min())

    lower_be_approx = cfg.middle_strike - wing_min + net_credit_per_unit
    upper_be_approx = cfg.middle_strike + wing_min - net_credit_per_unit

    metrics = {
        "p_lower": p_lower,
        "p_middle": p_middle,
        "p_upper": p_upper,
        "net_credit_per_unit": net_credit_per_unit,
        "total_credit": total_credit,
        "max_profit_approx": max_profit_approx,
        "max_loss_approx": max_loss_approx,
        "lower_be": lower_be_approx,
        "upper_be": upper_be_approx,
        "wing_1": wing_1,
        "wing_2": wing_2,
    }

    return metrics, df_pay


def render_short_butterfly(df_view: pd.DataFrame) -> None:
    """
    StrategyDefinition.render(df_view) – מצייר Short Butterfly.
    """

    st.markdown("### Short Butterfly (short 1:2:1)")

    if df_view is None or len(df_view) == 0:
        st.warning("אין נתונים ב-df_view. צריך לייצר שרשרת ולעבור את הפילטרים.")
        return

    required_cols = {"strike", "cp", "price"}
    if not required_cols.issubset(df_view.columns):
        st.error(f"df_view חייב להכיל עמודות: {required_cols}.")
        return

    cfg = _build_short_butterfly_ui(df_view)

    if not (cfg.lower_strike < cfg.middle_strike < cfg.upper_strike):
        st.error("חייבים לבחור lower < middle < upper בצורה מסודרת.")
        return

    try:
        metrics, df_pay = _compute_short_butterfly_payoff(cfg, df_view)
    except ValueError as e:
        st.error(str(e))
        return

    # --- מטריקות ---
    st.markdown("#### Results")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total credit (position)", f"{metrics['total_credit']:.2f}")
    c2.metric("Max profit (approx.)", f"{metrics['max_profit_approx']:.2f}")
    c3.metric("Max loss (on grid)", f"{metrics['max_loss_approx']:.2f}")

    c4, c5 = st.columns(2)
    c4.metric("Lower BE (approx.)", f"{metrics['lower_be']:.2f}")
    c5.metric("Upper BE (approx.)", f"{metrics['upper_be']:.2f}")

    st.caption(
        f"Lower={metrics['p_lower']:.2f} | "
        f"Middle={metrics['p_middle']:.2f} | "
        f"Upper={metrics['p_upper']:.2f} | "
        f"Net credit / unit={metrics['net_credit_per_unit']:.2f}"
    )

    # --- גרף payoff ---
    st.markdown("#### Payoff at expiry")

    fig = px.line(df_pay, x="S", y="P/L", title="Short Butterfly payoff (expiry)")
    fig.add_hline(y=0)
    st.plotly_chart(fig, use_container_width=True)
