# Layer: strategies
# core/straddle.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px


LegType = Literal["CALL", "PUT"]


@dataclass
class StraddleConfig:
    """קונפיגורציה בסיסית ל-Long Straddle אחד."""

    strike: float
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

    # אם יש bid/ask – mid, אחרת price
    if "bid" in row.columns and "ask" in row.columns:
        bid = float(row["bid"].iloc[0])
        ask = float(row["ask"].iloc[0])
        return 0.5 * (bid + ask)

    return float(row["price"].iloc[0])


def _build_straddle_ui(df_view: pd.DataFrame) -> StraddleConfig:
    """
    בונה UI קטן לבחירת סטרייק, כמות ומכפיל עבור Straddle.
    """
    st.markdown("#### Straddle parameters")

    strikes = sorted(df_view["strike"].unique().tolist())

    if len(strikes) == 0:
        st.warning("אין סטרייקים זמינים ב-df_view.")
        return StraddleConfig(strike=0.0, qty=1, multiplier=100)

    # נבחר סטרייק אמצעי כברירת מחדל (ATM-ish)
    mid_idx = len(strikes) // 2

    col_strike, col_qty, col_mult = st.columns(3)

    with col_strike:
        strike = st.selectbox(
            "Strike (CALL & PUT)",
            strikes,
            index=mid_idx,
            key="straddle_strike",
        )

    with col_qty:
        qty = st.number_input(
            "Contracts quantity",
            min_value=1,
            value=1,
            step=1,
            key="straddle_qty",
        )

    with col_mult:
        multiplier = st.number_input(
            "Contract multiplier",
            min_value=1,
            value=100,
            step=1,
            key="straddle_mult",
        )

    return StraddleConfig(
        strike=float(strike),
        qty=int(qty),
        multiplier=int(multiplier),
    )


def _compute_straddle_payoff(
    cfg: StraddleConfig, df_view: pd.DataFrame
) -> tuple[dict, pd.DataFrame]:
    """
    מחשב מטריקות ו-payoff ע"ג Long Straddle:
    Long CALL + Long PUT באותו סטרייק, כולל פרמיות מהשרשרת.
    """

    # מחירי CALL ו-PUT באותו סטרייק
    call_price = _find_mid_price(df_view, cfg.strike, "CALL")
    put_price = _find_mid_price(df_view, cfg.strike, "PUT")

    total_debit_per_unit = call_price + put_price  # עלות ליחידה
    total_debit = total_debit_per_unit * cfg.multiplier * cfg.qty

    # טווח מחירים S לגרף
    all_strikes = df_view["strike"].values
    s_min = float(all_strikes.min()) * 0.7
    s_max = float(all_strikes.max()) * 1.3
    S = np.linspace(s_min, s_max, 300)

    # payoff per 1 underlying
    payoff_call_unit = np.maximum(S - cfg.strike, 0.0)
    payoff_put_unit = np.maximum(cfg.strike - S, 0.0)
    payoff_unit = payoff_call_unit + payoff_put_unit - total_debit_per_unit

    # סקיילינג לכמות ומכפיל
    pl = payoff_unit * cfg.multiplier * cfg.qty

    df_pay = pd.DataFrame({"S": S, "P/L": pl})

    # Break-even points (בקירוב תיאורטי)
    lower_be = cfg.strike - total_debit_per_unit
    upper_be = cfg.strike + total_debit_per_unit

    max_loss = -total_debit
    max_profit = float(pl.max())  # בפועל תאורטית "אין גבול", אבל ניקח מהגרף

    metrics = {
        "call_price": call_price,
        "put_price": put_price,
        "total_debit_per_unit": total_debit_per_unit,
        "total_debit": total_debit,
        "max_profit": max_profit,
        "max_loss": max_loss,
        "lower_be": lower_be,
        "upper_be": upper_be,
    }

    return metrics, df_pay


def render_straddle(df_view: pd.DataFrame) -> None:
    """
    פונקציה שמתאימה ל-StrategyDefinition.render(df_view):
    מציירת את כל ה-UI של Long Straddle על בסיס df_view.
    """

    st.markdown("### Long Straddle")

    if df_view is None or len(df_view) == 0:
        st.warning("אין נתונים ב-df_view. צריך לייצר שרשרת ולעבור את הפילטרים.")
        return

    if "strike" not in df_view.columns or "cp" not in df_view.columns:
        st.error("df_view חייב להכיל עמודות 'strike' ו-'cp'.")
        return

    cfg = _build_straddle_ui(df_view)

    try:
        metrics, df_pay = _compute_straddle_payoff(cfg, df_view)
    except ValueError as e:
        st.error(str(e))
        return

    # --- הצגת מטריקות ---
    st.markdown("#### Results")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total debit (position)", f"{metrics['total_debit']:.2f}")
    c2.metric("Max loss", f"{metrics['max_loss']:.2f}")
    c3.metric("Max profit (on grid)", f"{metrics['max_profit']:.2f}")

    c4, c5 = st.columns(2)
    c4.metric("Lower BE", f"{metrics['lower_be']:.2f}")
    c5.metric("Upper BE", f"{metrics['upper_be']:.2f}")

    st.caption(
        f"Call price: {metrics['call_price']:.2f} | "
        f"Put price: {metrics['put_price']:.2f} | "
        f"Total debit per unit: {metrics['total_debit_per_unit']:.2f}"
    )

    # --- גרף payoff ---
    st.markdown("#### Payoff at expiry")

    fig = px.line(df_pay, x="S", y="P/L", title="Long Straddle payoff (expiry)")
    fig.add_hline(y=0)
    st.plotly_chart(fig, use_container_width=True)
