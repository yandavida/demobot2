# pages/1_strategy_workspace.py
# -----------------------------------------
# Strategy Workspace – SaaS V1 (API only)
# כל החישובים נעשים דרך /v1/position/analyze
# + Strategy Planner – /v1/strategy/suggest
# -----------------------------------------

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import streamlit as st

from ui.api_client import (
    analyze_position_v1,
    suggest_strategies_v1,
    ApiError,
)


# =========================
# Session Init
# =========================


def _init_session_state() -> None:
    """מאפס/יוצר אובייקט ברירת מחדל לטבלת ה־Legs."""
    if "builder_legs_df" not in st.session_state:
        st.session_state["builder_legs_df"] = pd.DataFrame(
            [
                {
                    "side": "SELL",
                    "cp": "C",  # C = Call, P = Put
                    "strike": 5000.0,
                    "quantity": 1,
                    "premium": 0.0,
                }
            ]
        )


# =========================
# Sidebar – Market Settings
# =========================


def render_market_sidebar() -> Dict[str, Any]:
    st.sidebar.header("הגדרות שוק וחישוב")

    symbol = st.sidebar.text_input(
        "סימול נכס בסיס (Symbol)",
        value="SPY",
        key="ws_symbol",
    )

    spot = st.sidebar.number_input(
        "מחיר נכס בסיס (Spot)",
        value=5000.0,
        step=10.0,
        format="%.2f",
        key="ws_spot",
    )

    col_range1, col_range2 = st.sidebar.columns(2)
    with col_range1:
        lower_factor = st.number_input(
            "טווח תחתון (x Spot)",
            value=0.8,
            step=0.05,
            format="%.2f",
            key="ws_lower_factor",
        )
    with col_range2:
        upper_factor = st.number_input(
            "טווח עליון (x Spot)",
            value=1.2,
            step=0.05,
            format="%.2f",
            key="ws_upper_factor",
        )

    num_points = st.sidebar.slider(
        "כמות נקודות בגרף",
        min_value=21,
        max_value=201,
        value=81,
        step=2,
        key="ws_num_points",
    )

    dte_days = st.sidebar.number_input(
        "ימים לפקיעה (DTE)",
        value=30,
        step=1,
        min_value=1,
        key="ws_dte_days",
    )

    iv = st.sidebar.number_input(
        "סטיית תקן (IV, באחוזים)",
        value=20.0,
        step=1.0,
        format="%.2f",
        key="ws_iv",
    )

    r = st.sidebar.number_input(
        "ריבית חסרת סיכון שנתית (r, באחוזים)",
        value=4.0,
        step=0.25,
        format="%.2f",
        key="ws_r",
    )

    q = st.sidebar.number_input(
        "תשואת דיבידנד שנתית (q, באחוזים)",
        value=0.0,
        step=0.25,
        format="%.2f",
        key="ws_q",
    )

    contract_multiplier = st.sidebar.number_input(
        "מכפיל חוזה (Contract Multiplier)",
        value=1.0,
        step=1.0,
        format="%.2f",
        key="ws_contract_multiplier",
    )

    invested_override = st.sidebar.number_input(
        "הון מושקע Override (לא חובה)",
        value=0.0,
        step=100.0,
        format="%.2f",
        key="ws_invested_override",
    )
    invested_override_val: float | None = (
        None if invested_override == 0.0 else invested_override
    )

    return {
        "symbol": symbol,
        "spot": spot,
        "lower_factor": lower_factor,
        "upper_factor": upper_factor,
        "num_points": num_points,
        "dte_days": dte_days,
        "iv": iv / 100.0,  # המרה לפרופורציה
        "r": r / 100.0,
        "q": q / 100.0,
        "contract_multiplier": contract_multiplier,
        "invested_override": invested_override_val,
    }


# =========================
# Legs Editor
# =========================


def render_legs_editor() -> pd.DataFrame:
    st.subheader("בונה פוזיציה חופשי (Legs)")
    st.caption("ערכי BUY/SELL, C/P, מחיר מימוש, כמות ופרמיה לכל Leg.")

    df: pd.DataFrame = st.session_state["builder_legs_df"]

    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        key="ws_legs_editor",
        column_config={
            "side": st.column_config.SelectboxColumn(
                "Side",
                options=["BUY", "SELL"],
                required=True,
            ),
            "cp": st.column_config.SelectboxColumn(
                "Type (C/P)",
                options=["C", "P"],
                required=True,
            ),
            "strike": st.column_config.NumberColumn(
                "Strike",
                format="%.2f",
            ),
            "quantity": st.column_config.NumberColumn(
                "Qty",
                format="%d",
            ),
            "premium": st.column_config.NumberColumn(
                "Premium",
                format="%.2f",
            ),
        },
    )

    st.session_state["builder_legs_df"] = edited_df.copy()
    return edited_df


# =========================
# Analysis Rendering
# =========================


def _auto_pick_xy(curve_df: pd.DataFrame) -> tuple[str, str] | None:
    """בחירה אוטומטית של X,Y לעקומה לפי עמודות נומריות."""
    if curve_df.empty:
        return None
    numeric_cols = [
        c for c in curve_df.columns if pd.api.types.is_numeric_dtype(curve_df[c])
    ]
    if len(numeric_cols) < 2:
        return None
    return numeric_cols[0], numeric_cols[1]


def render_analysis_outputs(analysis: Dict[str, Any]) -> None:
    if not analysis:
        st.warning("לא התקבלו נתונים מה־API.")
        return

    # קריאת שדות מה־API
    pl_summary: Dict[str, Any] = analysis.get("pl_summary") or {}
    greeks: Dict[str, Any] = analysis.get("greeks") or {}
    risk_profile: Dict[str, Any] = analysis.get("risk_profile") or {}
    be_points = analysis.get("break_even_points") or []
    curve = analysis.get("curve") or []
    scenarios = analysis.get("scenarios") or []
    strategy_name = analysis.get("strategy_name", "Unclassified Strategy")
    strategy_subtype = analysis.get("strategy_subtype", "")
    strategy_desc = analysis.get("strategy_description", "")
    risk_warnings = analysis.get("risk_warnings") or []
    validation_warnings = analysis.get("validation_warnings") or []

    # ===== כותרת אסטרטגיה + Risk =====
    top_col1, top_col2 = st.columns([3, 2])

    with top_col1:
        st.subheader(f"סיכום אסטרטגיה – {strategy_name}")
        if strategy_subtype:
            st.caption(f"Subtype: {strategy_subtype}")
        if strategy_desc:
            st.write(strategy_desc)

    with top_col2:
        st.markdown("#### Risk Profile (מה־API)")
        if risk_profile:
            level = risk_profile.get("level", "N/A")
            score = risk_profile.get("score", None)
            st.write(f"**Level:** {level}")
            if score is not None:
                st.write(f"**Score:** {score}")
            extra = {
                k: v
                for k, v in risk_profile.items()
                if k not in {"level", "score"} and v is not None
            }
            if extra:
                st.json(extra)
        else:
            st.info("בהחזרה אין Risk Profile.")

        if risk_warnings:
            st.markdown("**Risk Warnings:**")
            for w in risk_warnings:
                st.warning(str(w))

    st.markdown("---")

    if validation_warnings:
        st.markdown("**Validation Checks:**")
        for w in validation_warnings:
            st.warning(f"Validation: {w}")

    # ===== P&L, Greeks, BE =====
    m1, m2, m3 = st.columns(3)

    with m1:
        st.markdown("### P&L Summary")
        if pl_summary:
            st.json(pl_summary)
        else:
            st.info("בהחזרה אין pl_summary נתוני.")

    with m2:
        st.markdown("### Greeks")
        if greeks:
            st.json(greeks)
        else:
            st.info("בהחזרה אין Greeks נתוני.")

    with m3:
        st.markdown("### Break-even Points")
        if be_points:
            for i, v in enumerate(be_points, start=1):
                st.write(f"BE #{i}: {v}")
        else:
            st.info("אין נקודות איזון בהחזרה.")

    st.markdown("---")

    # ===== Curve =====
    st.markdown("### עקומת P&L (מה־API)")

    curve_df = pd.DataFrame(curve)
    if curve_df.empty:
        st.info("מה־API לא התקבלה עקומת curve.")
    else:
        xy = _auto_pick_xy(curve_df)
        if xy is None:
            st.dataframe(curve_df, use_container_width=True)
            st.info("לא נמצאו מספיק עמודות נומריות לגרף, מוצגת טבלה בלבד.")
        else:
            x_col, y_col = xy
            fig = px.line(curve_df, x=x_col, y=y_col)
            fig.update_layout(
                xaxis_title=x_col,
                yaxis_title=y_col,
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True)
            with st.expander("טבלת curve מלאה"):
                st.dataframe(curve_df, use_container_width=True)

    st.markdown("---")

    # ===== Scenarios =====
    st.markdown("### תרחישים (Scenarios)")

    scenarios_df = pd.DataFrame(scenarios)
    if scenarios_df.empty:
        st.info("מה־API לא התקבלו תרחישים.")
    else:
        st.dataframe(scenarios_df, use_container_width=True)


# =========================
# Strategy Planner – UI
# =========================


def render_planner_inputs(
    market_params: Dict[str, Any]
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """UI ל-Goals + Market לצורך קריאה ל-/v1/strategy/suggest."""
    st.subheader("Strategy Planner – Goals & Market Snapshot")
    st.caption("המלצות אסטרטגיה מתוך SaaS Planner לפי מטרות, סיכון וכיוון שוק.")

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        account_size = st.number_input(
            "גודל חשבון משוער",
            min_value=0.0,
            value=100_000.0,
            step=10_000.0,
            format="%.2f",
            key="planner_account_size",
        )
        risk_tolerance = st.selectbox(
            "רמת סיכון רצויה",
            options=["low", "medium", "high"],
            index=1,
            key="planner_risk_tolerance",
        )
        view = st.selectbox(
            "כיוון שוק",
            options=["bullish", "bearish", "neutral", "range"],
            index=0,
            key="planner_view",
        )
        time_horizon_days = st.slider(
            "טווח זמן רצוי (ימים)",
            min_value=1,
            max_value=365,
            value=int(market_params.get("dte_days", 30)),
            key="planner_time_horizon",
        )

    with col_g2:
        target_profit_pct = st.number_input(
            "יעד תשואה על החשבון (%) – אופציונלי",
            min_value=0.0,
            value=5.0,
            step=0.5,
            format="%.2f",
            key="planner_target_profit_pct",
        )
        max_loss_pct = st.number_input(
            "הפסד מקסימלי נסבל (%) – אופציונלי",
            min_value=0.0,
            value=3.0,
            step=0.5,
            format="%.2f",
            key="planner_max_loss_pct",
        )
        allow_short_options = st.checkbox(
            "לאפשר כתיבת אופציות (Short Options)",
            value=True,
            key="planner_allow_short",
        )
        allow_multi_leg = st.checkbox(
            "לאפשר אסטרטגיות מרובות רגליים (Multi-leg)",
            value=True,
            key="planner_allow_multi",
        )

    goals: Dict[str, Any] = {
        "account_size": account_size,
        "risk_tolerance": risk_tolerance,
        "view": view,
        "time_horizon_days": int(time_horizon_days),
        "target_profit_pct": target_profit_pct or None,
        "max_loss_pct": max_loss_pct or None,
        "allow_short_options": bool(allow_short_options),
        "allow_multi_leg": bool(allow_multi_leg),
    }

    # Market snapshot ל-Planner
    expiry = date.today() + timedelta(days=int(time_horizon_days))
    market: Dict[str, Any] = {
        "symbol": market_params.get("symbol", "SPY"),
        "spot": market_params.get("spot", 0.0),
        "expiry": expiry.isoformat(),
        "iv": market_params.get("iv", None),
        "r": market_params.get("r", None),
        "q": market_params.get("q", None),
    }

    return goals, market


def render_planner_strategies(strategies: List[Dict[str, Any]]) -> None:
    """מציג את האסטרטגיות שהוחזרו מה-Planner API."""
    if not strategies:
        st.info("לא הוחזרו אסטרטגיות מה-Planner.")
        return

    st.markdown("### אסטרטגיות מומלצות")

    for i, s in enumerate(strategies, start=1):
        name = s.get("name", f"Strategy #{i}")
        subtype = s.get("subtype", "")
        risk_score = s.get("risk_score", None)
        payoff = s.get("payoff_summary") or {}
        legs = s.get("legs") or []
        tokens = s.get("explanation_tokens") or []

        with st.expander(f"{i}. {name} – {subtype}", expanded=(i == 1)):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("**Legs**")
                if legs:
                    legs_df = pd.DataFrame(legs)
                    st.dataframe(legs_df, use_container_width=True, hide_index=True)
                else:
                    st.write("אין רגליים בהחזרה.")

                st.markdown("**Payoff Summary**")
                if payoff:
                    st.json(payoff)
                else:
                    st.write("אין Payoff Summary בהחזרה.")

            with col2:
                st.markdown("**Risk Score**")
                if risk_score is not None:
                    st.metric(
                        "Risk Score (0–1)",
                        f"{float(risk_score):.2f}",
                    )
                else:
                    st.write("לא הוחזר risk_score.")

                st.markdown("**Explanation**")
                if tokens:
                    for t in tokens:
                        st.write(f"- {t}")
                else:
                    st.write("אין טקסט הסבר בהחזרה.")


# =========================
# Main Page
# =========================


def main() -> None:
    # אם יש לך כבר page_config ב-app.py אפשר להסיר את השורה הבאה
    st.set_page_config(
        page_title="Strategy Workspace – SaaS",
        layout="wide",
    )

    _init_session_state()

    st.title("Strategy Workspace (SaaS v2)")
    st.caption(
        "כל חישובי ה-P/L נעשים דרך /v1/position/analyze, "
        "וההמלצות האסטרטגיות דרך /v1/strategy/suggest."
    )

    # Sidebar – Market
    market_params = render_market_sidebar()

    # Legs Editor
    edited_df = render_legs_editor()

    st.markdown("---")

    # כפתור קריאה ל־API – Position Analyze
    if st.button("Analyze via SaaS API", type="primary", key="btn_analyze_position"):
        if edited_df.empty:
            st.warning("לא הוגדר אף Leg בפוזיציה.")
            return

        with st.spinner("מריץ חישוב דרך ה־SaaS API..."):
            try:
                analysis = analyze_position_v1(
                    edited_df,
                    spot=market_params["spot"],
                    lower_factor=market_params["lower_factor"],
                    upper_factor=market_params["upper_factor"],
                    num_points=market_params["num_points"],
                    dte_days=market_params["dte_days"],
                    iv=market_params["iv"],
                    r=market_params["r"],
                    q=market_params["q"],
                    contract_multiplier=market_params["contract_multiplier"],
                    invested_override=market_params["invested_override"],
                )
            except Exception as e:
                st.error(f"שגיאה בקריאה ל־API: {e}")
                return

        render_analysis_outputs(analysis)

    st.markdown("## Strategy Planner – SaaS")

    # Goals + Market ל-Planner
    goals, planner_market = render_planner_inputs(market_params)

    # כפתור קריאה ל־Planner API (SaaS)
    if st.button("Suggest Strategies (Planner API)", type="primary"):
        if edited_df.empty:
            st.warning("לא הוגדר אף Leg בפוזיציה.")
            return

        # כאן נשאר כל הקוד שיש לך לבנייה של goals ו-market_params
        # ...
        # נניח שבסוף יצרת:
        #   goals = ...
        #   planner_market = ...

        with st.spinner("מריץ מנוע Planner בענן (SaaS)..."):
            try:
                planner_resp = suggest_strategies_v1(
                    goals=goals,
                    market=planner_market,
                )
                strategies = planner_resp.get("strategies", [])
                render_planner_strategies(strategies)

            except ApiError as e:
                # API-שגיאות ייעודיות מהשכבה האנליטית
                if e.error_type == "auth":
                    st.error("שגיאת התחברות ל-SaaS – בדקי API Key / הרשאות.")
                elif e.error_type == "validation":
                    st.error(
                        "שגיאת ולידציה בנתונים (validation). בדקי את הפרמטרים שנשלחו ל-API."
                    )
                    with st.expander("פרטי ולידציה מלאים"):
                        st.write(e.details)
                elif e.error_type == "timeout":
                    st.warning(
                        "חריגה מזמן ההמתנה למנוע. אפשר לנסות שוב בעוד מספר שניות."
                    )
                elif e.error_type == "server":
                    st.error("שגיאת שרת בצד המנוע (5xx). אם זה נמשך – לפנות לתמיכה.")
                else:
                    st.error(f"שגיאת API לא צפויה: {e.message}")
                    if e.details:
                        with st.expander("פרטי שגיאה גולמיים"):
                            st.write(e.details)

            except Exception as e:
                # ביטוח כללי – לא משאירים Exception בלי טיפול
                st.error(f"שגיאה לא צפויה ב-UI: {e}")
                return

        planner_resp = suggest_strategies_v1(goals=goals, market=planner_market)
        strategies = planner_resp.get("strategies", [])
        render_planner_strategies(strategies)


if __name__ == "__main__":
    main()
