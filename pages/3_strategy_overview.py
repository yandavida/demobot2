# pages/3_strategy_overview.py
# Layer: ui

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
import streamlit as st

# ערכת נושא + Header גלובלי (אם קיימים)
try:
    from ui.theme import apply_global_theme, render_app_header
except ImportError:  # אם אין – לא ניפול
    apply_global_theme = None
    render_app_header = None

# פונקציות UI בלבד (לא חישוביות)
from ui.strategy_services import make_builder_figures
from ui.api_client import analyze_position_v1, ApiError


# ---------------------------------------------------
#  Helpers
# ---------------------------------------------------
def _get_strategy_params() -> Dict[str, Any]:
    """
    קריאת פרמטרי פרופיל האסטרטגיה מה-session_state בצורה בטוחה
    עם המרות וערכי ברירת מחדל.
    """
    raw: Dict[str, Any] = st.session_state.get("strategy_params", {}) or {}

    def _to_float(value: Any, default: float) -> float:
        try:
            if value is None or value == "":
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def _to_int(value: Any, default: int) -> int:
        try:
            if value is None or value == "":
                return default
            return int(value)
        except (TypeError, ValueError):
            return default

    return {
        "target_profit_pct": _to_float(raw.get("target_profit_pct"), 0.0),
        "max_loss_pct": _to_float(raw.get("max_loss_pct"), 0.0),
        "dte": _to_int(raw.get("dte"), 0),
        "aggressiveness": _to_int(raw.get("aggressiveness"), 0),
        "market_view": str(raw.get("market_view") or ""),
        "spot": _to_float(raw.get("spot"), 0.0),
    }


# ---------------------------------------------------
#  Section 1 – תקציר פרופיל העסקה והאסטרטגיות שהוצעו
# ---------------------------------------------------
def render_profile_and_suggestions_section() -> None:
    """Render strategy profile and suggestions side by side from session state."""
    profile = st.session_state.get("strategy_profile")
    raw_suggestions = st.session_state.get("strategy_suggestions") or []
    suggestions: List[Dict[str, Any]] = list(raw_suggestions)

    profile_col, suggestions_col = st.columns([1, 1])

    # צד שמאל – פרופיל האסטרטגיה (JSON גולמי)
    with profile_col:
        st.subheader("Strategy profile")
        if profile is not None:
            st.json(profile)
        else:
            st.info("No profile available yet.")

    # צד ימין – רשימת המלצות (טקסט)
    with suggestions_col:
        st.subheader("Suggestions")
        if suggestions:
            for suggestion in suggestions:
                name = suggestion.get("name") if isinstance(suggestion, dict) else None
                line = name or str(suggestion)
                st.write(f"- {line}")
        else:
            st.info("No suggestions yet.")

    # סיכום פרופיל + טבלת אסטרטגיות
    col_l, col_r = st.columns([1, 2])

    # פרמטרים שהוגדרו בפרופיל
    params = _get_strategy_params()

    with col_l:
        st.markdown("#### פרופיל שהוגדר")
        st.markdown(
            f"""
            - יעד רווח: **{params['target_profit_pct']:.1f}%**  
            - הפסד מקסימלי: **{params['max_loss_pct']:.1f}%**  
            - ימים לפקיעה (DTE): **{params['dte']}**  
            - רמת אגרסיביות: **{params['aggressiveness']} / 10**  
            - תפיסת שוק: **{params['market_view']}**  
            - Spot נוכחי לחישוב: **{params['spot']:,.2f}**
            """
        )

    # תקציר אסטרטגיות – טבלה
    with col_r:
        st.markdown("#### תקציר האסטרטגיות שהוצעו")

        if not suggestions:
            st.info("לא קיימות אסטרטגיות מוצעות להצגה.")
            return

        rows: List[Dict[str, Any]] = []

        for idx, sug in enumerate(suggestions[:5]):
            if not isinstance(sug, dict):
                # אם המבנה שונה – נציג אותו כטקסט בלבד
                rows.append(
                    {
                        "שם אסטרטגיה": f"Strategy #{idx + 1}",
                        "רווח מקסימלי (תיאורטי)": "",
                        "הפסד מקסימלי (תיאורטי)": "",
                        "R/R": "",
                        "מס' נקודות BE": "",
                    }
                )
                continue

            summary = sug.get("summary") or {}
            max_profit = float(summary.get("max_profit", 0.0) or 0.0)
            max_loss = float(summary.get("max_loss", 0.0) or 0.0)
            be_points = summary.get("break_even_points") or []

            rr: float | None
            if max_loss != 0:
                rr = abs(max_profit / max_loss)
            else:
                rr = None

            rows.append(
                {
                    "שם אסטרטגיה": sug.get("name", f"Strategy #{idx + 1}"),
                    "רווח מקסימלי (תיאורטי)": max_profit * 100,
                    "הפסד מקסימלי (תיאורטי)": max_loss * 100,
                    "R/R": rr,
                    "מס' נקודות BE": len(be_points),
                }
            )

        df_view = pd.DataFrame(rows)
        st.dataframe(df_view, use_container_width=True, hide_index=True)


# ---------------------------------------------------
#  Section 2 – תקציר הפוזיציה הנוכחית מה-Builder (דרך SaaS API)
# ---------------------------------------------------
def render_builder_snapshot_section() -> None:
    st.subheader("תקציר הפוזיציה הנוכחית (מה-Builder)")

    legs_df = st.session_state.get("legs_df")
    if legs_df is None or not isinstance(legs_df, pd.DataFrame) or legs_df.empty:
        st.info(
            "אין כרגע פוזיציה ב-Builder. אפשר להגדיר רגליים בטאב 'Strategy Workspace'."
        )
        return

    # אותם פרמטרים כמו ב-Builder (נשלפים מה-session)
    spot = st.session_state.get("builder_spot", 5000.0)
    lower_factor = st.session_state.get("builder_lower_factor", 0.8)
    upper_factor = st.session_state.get("builder_upper_factor", 1.2)
    num_points = st.session_state.get("builder_num_points", 201)
    dte_days = st.session_state.get("builder_dte", 30)
    iv_pct = st.session_state.get("builder_iv", 20.0)
    r_pct = st.session_state.get("builder_r", 2.0)
    q_pct = st.session_state.get("builder_q", 0.0)
    contract_multiplier = st.session_state.get("builder_multiplier", 100)

    # הון מושקע (אם המשתמשת הגדירה בטאב Builder)
    invested_input = st.session_state.get("builder_invested", 0.0)
    invested_override = (
        float(invested_input) if invested_input and invested_input > 0 else None
    )

    r = r_pct / 100.0
    q = q_pct / 100.0
    iv = iv_pct / 100.0

    # קריאה ל-SaaS API (במקום run_builder_analysis המקומי)
    try:
        analysis: Dict[str, Any] = analyze_position_v1(
            legs_df,
            spot=spot,
            lower_factor=lower_factor,
            upper_factor=upper_factor,
            num_points=num_points,
            dte_days=dte_days,
            iv=iv,
            r=r,
            q=q,
            contract_multiplier=contract_multiplier,
            invested_override=invested_override,
        )

    except ApiError as e:
        # טיפול חכם לפי סוג השגיאה
        if e.error_type == "auth":
            st.error("שגיאת התחברות ל־SaaS (API Key / הרשאות).")
        elif e.error_type == "validation":
            st.error(
                "שגיאת ולידציה בנתונים שנשלחו ל־API – בדקי את הרגליים (Legs) והפרמטרים."
            )
        elif e.error_type == "timeout":
            st.warning(
                "חריגה מזמן ההמתנה לשרת (timeout). אפשר לנסות שוב בעוד מספר שניות."
            )
        elif e.error_type == "server":
            st.error("שגיאת שרת בצד המנוע (5xx). אם זה חוזר – כדאי לפנות לתמיכה.")
        else:
            st.error(f"שגיאת API לא צפויה: {e}")

        with st.expander("פרטי שגיאה טכנית (אופציונלי)", expanded=False):
            if hasattr(e, "to_dict"):
                st.write(e.to_dict())
            else:
                st.write(str(e))

        return

    except Exception as e:  # noqa: BLE001
        # כל שגיאה אחרת – באג ב-UI / לוגיקה
        st.error(f"שגיאה לא צפויה ב-UI/ניתוח הפוזיציה: {e}")
        return

    # מיפוי תשובת ה-API לאותם משתנים שה-UI מצפה להם
    curve_df = pd.DataFrame(analysis.get("curve") or [])
    be_points = analysis.get("break_even_points") or []
    scenarios_df = pd.DataFrame(analysis.get("scenarios") or [])
    pl_summary: Dict[str, Any] = analysis.get("pl_summary") or {}
    greeks: Dict[str, Any] = analysis.get("greeks") or {}
    risk_profile: Dict[str, Any] = analysis.get("risk_profile") or {}
    strategy_name = analysis.get("strategy_name", "אסטרטגיה לא מזוהה")
    strategy_subtype = analysis.get("strategy_subtype")
    strategy_description = analysis.get("strategy_description")
    net_credit = float(analysis.get("net_credit", 0.0) or 0.0)
    total_credit = float(analysis.get("total_credit", 0.0) or 0.0)
    risk_warnings: List[str] = analysis.get("risk_warnings") or []

    invested_capital = float(pl_summary.get("invested_capital", 0.0) or 0.0)
    max_profit = float(pl_summary.get("max_profit", 0.0) or 0.0)
    max_loss = float(pl_summary.get("max_loss", 0.0) or 0.0)
    max_profit_pct = float(pl_summary.get("max_profit_pct", 0.0) or 0.0)
    max_loss_pct = float(pl_summary.get("max_loss_pct", 0.0) or 0.0)
    pl_at_spot = float(pl_summary.get("pl_at_spot", 0.0) or 0.0)
    pl_spot_pct = float(pl_summary.get("pl_spot_pct", 0.0) or 0.0)
    rr_ratio = pl_summary.get("rr_ratio", None)

    # ---- כותרת: אסטרטגיה + צ'יפ סיכון ----
    col_top1, col_top2 = st.columns([2, 2])

    with col_top1:
        st.markdown(f"**אסטרטגיה מזוהה:** {strategy_name}")
        if strategy_subtype:
            st.markdown(f"**תת-סוג:** {strategy_subtype}")
        if strategy_description:
            st.caption(str(strategy_description))

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric(
                "רווח מקסימלי (תיאורטי)",
                f"{max_profit:,.2f}",
                f"{max_profit_pct:.1f}% מההון",
            )
        with col_m2:
            st.metric(
                "הפסד מקסימלי (תיאורטי)",
                f"{max_loss:,.2f}",
                f"{max_loss_pct:.1f}% מההון",
            )
        with col_m3:
            st.metric("R/R", f"{rr_ratio:.2f} : 1" if rr_ratio is not None else "N/A")

        be_str = (
            ", ".join(f"{x:,.2f}" for x in be_points) if be_points else "אין / לא זוהו"
        )
        st.markdown(f"**נקודות איזון (BE):** {be_str}")

        st.metric(
            "P/L בנקודת ה-Spot",
            f"{pl_at_spot:,.2f}",
            f"{pl_spot_pct:.1f}% מההון",
        )
        st.metric("קרדיט נטו (פר יחידה)", f"{net_credit:.2f}")
        st.caption(f"קרדיט כולל: {total_credit:.2f}")

    with col_top2:
        st.markdown("**Position Greeks (צילום מצב)**")
        col_g1, col_g2, col_g3, col_g4, col_g5 = st.columns(5)
        with col_g1:
            st.metric("Delta", f"{greeks.get('delta', 0.0):,.2f}")
        with col_g2:
            st.metric("Gamma", f"{greeks.get('gamma', 0.0):,.4f}")
        with col_g3:
            st.metric("Vega (ל-1% IV)", f"{greeks.get('vega', 0.0):,.2f}")
        with col_g4:
            st.metric("Theta (ליום)", f"{greeks.get('theta', 0.0):,.2f}")
        with col_g5:
            st.metric("Rho (ל-1% r)", f"{greeks.get('rho', 0.0):,.2f}")

        if risk_warnings:
            with st.expander("אזהרות סיכון לפי פרופיל הלקוח", expanded=True):
                for msg in risk_warnings:
                    st.write(f"• {msg}")

    # ---- גרף P/L ----
    st.markdown("#### גרף P/L כולל מכפיל")

    if not curve_df.empty:
        fig_full, _ = make_builder_figures(
            curve_df=curve_df,
            be_points=be_points,
            spot=spot,
            max_profit=max_profit,
        )
        if fig_full is not None:
            st.plotly_chart(fig_full, use_container_width=True)
    else:
        st.info("לא זמינה עקומת P/L להצגה.")

    # ---- טבלת תרחישים (high level בלבד) ----
    st.markdown("#### תרחישי מחיר (צילום מה-Builder)")

    if not scenarios_df.empty:
        st.dataframe(scenarios_df, use_container_width=True, hide_index=True)
    else:
        st.info("לא זמינים תרחישי מחיר להצגה.")


# ---------------------------------------------------
#  main
# ---------------------------------------------------
def main() -> None:
    if apply_global_theme is not None:
        apply_global_theme()

    if render_app_header is not None:
        render_app_header(
            "Strategy Overview",
            "צילום מצב מסכם של פרופיל העסקה והפוזיציה הנוכחית",
        )
    else:
        st.title("Strategy Overview")

    render_profile_and_suggestions_section()
    st.markdown("---")
    render_builder_snapshot_section()


if __name__ == "__main__":
    main()
