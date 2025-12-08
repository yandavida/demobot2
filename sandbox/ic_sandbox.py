# core/ic_sandbox.py
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from core.models import IronCondorInput
from core.pricing import iron_condor_expiry_payoff_curve


def render_ic_sandbox(df_view: pd.DataFrame) -> None:
    """UI + חישובים ל־Iron Condor על בסיס df_view המסונן."""
    from core.strategies_legacy import iron_condor_metrics

    if df_view is None or len(df_view) == 0:
        st.info("אין נתונים אחרי סינון – צרי chain ותסנני לפני סימולציה.")
        return

    puts = df_view[df_view["cp"] == "PUT"].sort_values("strike")
    calls = df_view[df_view["cp"] == "CALL"].sort_values("strike")

    if puts.empty or calls.empty:
        st.warning("צריך גם PUT וגם CALL ב־df_view בשביל Iron Condor.")
        return

    # ===== בחירת סטרייקים =====
    colA, colB, colC, colD = st.columns(4)
    with colA:
        sp = st.selectbox(
            "Short PUT strike",
            puts["strike"].unique().tolist(),
            key="ic_sp",
        )
    with colB:
        lp = st.selectbox(
            "Long PUT strike",
            puts["strike"].unique().tolist(),
            key="ic_lp",
        )
    with colC:
        sc = st.selectbox(
            "Short CALL strike",
            calls["strike"].unique().tolist(),
            key="ic_sc",
        )
    with colD:
        lc = st.selectbox(
            "Long CALL strike",
            calls["strike"].unique().tolist(),
            key="ic_lc",
        )

    qty = st.number_input(
        "Quantity (contracts)",
        min_value=1,
        value=1,
        step=1,
        key="ic_qty",
    )
    mult = st.number_input(
        "Contract multiplier",
        min_value=1,
        value=100,
        step=1,
        key="ic_mult",
    )

    # ניסוי לקבל ספוט דיפולטי מהדאטה, אם יש
    if "underlying_price" in df_view.columns and len(df_view) > 0:
        default_spot = float(df_view["underlying_price"].iloc[0])
    else:
        default_spot = 0.0

    spot = st.number_input(
        "Spot price",
        min_value=0.0,
        value=default_spot,
        step=0.5,
        key="ic_spot",
    )

    # ===== חישוב מדדים ו־payoff =====
    try:
        ic = IronCondorInput(
            short_put_strike=float(sp),
            long_put_strike=float(lp),
            short_call_strike=float(sc),
            long_call_strike=float(lc),
            qty=int(qty),
            multiplier=int(mult),
            spot=float(spot),
        )

        # קריאה לפונקציות החישוב בפירוט (לפי החתימה הקיימת ב-core.strategies / core.pricing)
        metrics, df_pay = iron_condor_metrics(
            df_view,
            ic.short_put_strike,
            ic.long_put_strike,
            ic.short_call_strike,
            ic.long_call_strike,
            ic.qty,
            ic.multiplier,
            ic.spot,
        )

        # חישוב עקומת ה־P/L לפקיעה
        df_pay = iron_condor_expiry_payoff_curve(df_view, ic)

    except ValueError as e:
        st.error(f"⚠ {e}")
        st.stop()
        return

    # ===== הצגת מדדים =====
    colA, colB, colC = st.columns(3)
    colA.metric("Net credit (per unit)", f"{metrics.net_credit:.2f}")
    colB.metric("Max profit (per unit)", f"{metrics.max_profit_per_unit:.2f}")
    colC.metric("Max loss (per unit)", f"{metrics.max_loss_per_unit:.2f}")

    st.caption(f"Break-even points: {metrics.lower_be:.2f} / {metrics.upper_be:.2f}")

    # ===== גרף Payoff =====
    fig_ic = px.line(df_pay, x="S", y="P/L", title="Iron Condor payoff (expiry)")
    fig_ic.add_hline(y=0)
    fig_ic.add_vline(x=ic.spot, line_dash="dot")
    st.plotly_chart(fig_ic, use_container_width=True, key="ic_payoff")
