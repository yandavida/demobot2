# Layer: ui
# pages/4_fx_workspace.py
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from core.fx_math import FxDealInput
from ui.api_client import analyze_fx_forward_v1, ApiError


# נסיון לטעון ערכת נושא ו־Header גלובלי
try:
    from ui.theme import apply_global_theme, render_app_header
except ImportError:  # אם אין, פשוט נתעלם
    apply_global_theme = None
    render_app_header = None


def _build_fx_deal_from_inputs() -> FxDealInput:
    """
    קורא את ערכי ה-UI ובונה FxDealInput אחד.
    זה הממשק בין ה-UI להגדרת עסקה בודדת (Forward).
    """
    pair = st.session_state.get("fx_pair", "EURUSD")
    notional = st.session_state.get("fx_notional", 1_000_000.0)
    direction_raw = st.session_state.get("fx_direction", "buy")
    forward_rate = st.session_state.get("fx_forward", 1.10)
    spot_today = st.session_state.get("fx_spot", 1.09)
    maturity_days = int(st.session_state.get("fx_maturity", 30))

    direction = "buy" if direction_raw == "buy" else "sell"

    return FxDealInput(
        pair=pair,
        notional=float(notional),
        direction=direction,  # type: ignore[arg-type]
        forward_rate=float(forward_rate),
        spot_today=float(spot_today),
        maturity_days=maturity_days,
    )


def _render_inputs_panel() -> FxDealInput:
    """פאנל הקלט בצד שמאל – חוזה Forward אחד."""
    st.sidebar.header("הגדרות עסקת FX")

    st.sidebar.text_input(
        "צמד מטבעות (pair)",
        value="EURUSD",
        key="fx_pair",
        help="למשל EURUSD, USDILS, GBPUSD וכו'.",
    )

    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.selectbox(
            "כיוון עסקה",
            options=["buy", "sell"],
            index=0,
            key="fx_direction",
            help="buy = קניית מטבע בסיס, sell = מכירה.",
        )
    with col2:
        st.number_input(
            "נומינלי (base)",
            min_value=1_000.0,
            max_value=100_000_000.0,
            value=1_000_000.0,
            step=50_000.0,
            key="fx_notional",
        )

    st.sidebar.number_input(
        "שער Spot נוכחי",
        min_value=0.0001,
        max_value=1_000.0,
        value=1.09,
        step=0.0001,
        format="%.4f",
        key="fx_spot",
    )

    st.sidebar.number_input(
        "שער Forward (שער עסקה)",
        min_value=0.0001,
        max_value=1_000.0,
        value=1.10,
        step=0.0001,
        format="%.4f",
        key="fx_forward",
        help="השער שסוכם בהסכם ה-Forward.",
    )

    st.sidebar.number_input(
        "ימים לפקיעה",
        min_value=1,
        max_value=3650,
        value=30,
        step=1,
        key="fx_maturity",
    )

    st.sidebar.caption(
        "הטאב הזה מדמה עסקת Forward אחת בצורה פשוטה. "
        "בהמשך נוכל להרחיב לפורטפוליו מלא ולחיבור למערכות Treasury."
    )

    return _build_fx_deal_from_inputs()


def _split_pair(pair: str) -> tuple[str, str]:
    """
    מפצל צמד כמו EURUSD ל-base='EUR', quote='USD'.
    אם המבנה לא תקין – מחזיר מטבע quote דיפולטי.
    """
    p = pair.strip().upper()
    if len(p) >= 6:
        return p[:3], p[3:6]
    # fallback – נניח שהוא מול USD
    return p[:3], "USD"


def main() -> None:
    # ערכת נושא / Header אם יש
    if apply_global_theme is not None:
        apply_global_theme()

    if render_app_header is not None:
        render_app_header(
            "FX Workspace",
            'טאב פשוט לניתוח עסקת Forward אחת במט"ח',
        )
    else:
        st.title("FX Workspace – Forward אחד")

    # -------- קלט מה-Sidebar --------
    deal = _render_inputs_panel()

    # נגזור base/quote מתוך הצמד
    base_ccy, quote_ccy = _split_pair(deal.pair)

    # מיפוי לדרישות ה-API:
    _direction_api = "BUY" if deal.direction.lower() == "buy" else "SELL"
    valuation_date = date.today()
    _maturity_date = valuation_date + timedelta(days=deal.maturity_days)

    # -------- קריאה ל-API --------
    # -------- קריאה למנוע דרך שכבת ה-API --------
    try:
        analysis = analyze_fx_forward_v1(
            base_ccy=deal.pair[:3],
            quote_ccy=deal.pair[3:],
            notional=deal.notional,
            direction=deal.direction.upper(),  # BUY/SELL
            spot=deal.spot_today,
            forward_rate=deal.forward_rate,
            valuation_date=date.today(),
            maturity_date=date.today() + timedelta(days=deal.maturity_days),
            curve_min_pct=-0.1,
            curve_max_pct=0.1,
            curve_points=101,
        )
    except ApiError as e:
        if e.error_type == "auth":
            st.error("שגיאת התחברות למנוע ה-FX (API Key / הרשאות).")
        elif e.error_type == "validation":
            st.error("שגיאת ולידציה בעסקת ה-FX. בדקי את המטבעות, השערים והתאריכים.")
        elif e.error_type == "timeout":
            st.warning("חריגה מזמן ההמתנה למנוע ה-FX. נסי שוב בעוד מספר שניות.")
        elif e.error_type == "server":
            st.error("שגיאת שרת במנוע ה-FX. אם זה נמשך, פני לתמיכה.")
        else:
            st.error(f"שגיאת FX API: {e}")

        # אופציונלי: פרטים טכניים
        # with st.expander("פרטי שגיאה טכניים"):
        #     st.write(e.details)

        return

    except Exception as e:
        st.error(f"שגיאה לא צפויה ב-UI של FX Workspace: {e}")
        return

    # analysis הוא dict שמגיע מה-API:
    # {
    #   "curve": [{"underlying": ..., "pl": ...}, ...],
    #   "pl_summary": {...},
    #   "risk_profile": {...},
    #   "scenarios": [...]
    # }

    curve = analysis.get("curve", []) or []
    pl_summary = analysis.get("pl_summary", {}) or {}
    risk_profile = analysis.get("risk_profile", {}) or {}
    scenarios = analysis.get("scenarios", []) or []

    # נבנה DataFrame לעקום
    if curve:
        curve_df = pd.DataFrame(curve)
        # נוודא שיש עמודה price לגרף
        if "underlying" in curve_df.columns and "price" not in curve_df.columns:
            curve_df = curve_df.rename(columns={"underlying": "price"})
    else:
        curve_df = pd.DataFrame()

    # -------- סיכום עסקה --------
    st.subheader("סיכום עסקת FX")

    col_top1, col_top2, col_top3 = st.columns(3)
    with col_top1:
        st.metric("צמד", deal.pair)
        st.metric("נומינלי (base)", f"{deal.notional:,.0f}")
    with col_top2:
        st.metric("Spot נוכחי", f"{deal.spot_today:.4f}")
        st.metric("Forward (שער עסקה)", f"{deal.forward_rate:.4f}")
    with col_top3:
        st.metric("כיוון", "Long base" if deal.direction == "buy" else "Short base")
        st.metric("ימים לפקיעה", f"{deal.maturity_days} יום")

    # -------- מטריקות P/L --------
    st.markdown("### מדדי רווח/הפסד (ב-Quote currency)")

    pl_at_spot = float(pl_summary.get("pl_at_spot", 0.0))
    max_profit = float(pl_summary.get("max_profit", 0.0))
    max_loss = float(pl_summary.get("max_loss", 0.0))

    # הערכה פשוטה לשווי נומינלי ב-quote: notional * spot
    notional_value_quote = deal.notional * deal.spot_today

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("P/L לפי Spot נוכחי", f"{pl_at_spot:,.2f}")
    with col_m2:
        st.metric("רווח מקסימלי (בטווח שנבדק)", f"{max_profit:,.2f}")
    with col_m3:
        st.metric("הפסד מקסימלי (בטווח שנבדק)", f"{max_loss:,.2f}")
    with col_m4:
        st.metric("שווי נומינלי מקורב (quote)", f"{notional_value_quote:,.2f}")

    # -------- פרופיל סיכון --------
    st.markdown("### פרופיל סיכון בסיסי")

    level = risk_profile.get("risk_level", "n/a")
    score = risk_profile.get("risk_score", None)
    comments_list = risk_profile.get("comments", []) or []
    first_comment = comments_list[0] if comments_list else "אין הערות מיוחדות."

    col_r1, col_r2 = st.columns([0.3, 0.7])
    with col_r1:
        label = str(level).upper()
        if score is not None:
            label = f"{label} (score={score:.2f})"
        st.metric("רמת סיכון משוערת", label)
    with col_r2:
        st.write(first_comment)

    # -------- גרף P/L --------
    st.markdown('### עקומת P/L לפי שינוי בשער המט"ח')

    if (
        curve_df.empty
        or "price" not in curve_df.columns
        or "pl" not in curve_df.columns
    ):
        st.info("לא זמינה כרגע עקומת P/L (חסרים נתונים מהשרת).")
    else:
        fig = px.line(curve_df, x="price", y="pl")
        fig.update_layout(
            height=420,
            margin=dict(l=60, r=40, t=40, b=60),
            xaxis_title="שער Spot",
            yaxis_title="P/L במטבע ה-quote",
        )
        fig.add_hline(y=0, line_dash="dash")
        fig.add_vline(x=deal.spot_today, line_dash="dot")

        st.plotly_chart(fig, use_container_width=True)

        # -------- טבלת תרחישים --------
        with st.expander("טבלת תרחישים (לפתיחה באקסל)", expanded=False):
            if scenarios:
                scenarios_df = pd.DataFrame(scenarios)
                st.dataframe(
                    scenarios_df,
                    use_container_width=True,
                    hide_index=True,
                )
                csv = scenarios_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 הורדת תרחישים כ-CSV",
                    data=csv,
                    file_name=f"fx_forward_scenarios_{deal.pair}.csv",
                    mime="text/csv",
                )
            else:
                st.info("אין תרחישים זמינים מה-API (scenarios ריק).")


if __name__ == "__main__":
    main()
