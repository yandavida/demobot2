from __future__ import annotations

import pandas as pd
import streamlit as st
from typing import Any, Callable, Dict, Optional

from ui.api_client import (
    ApiError,
    create_arbitrage_session,
    get_arbitrage_history,
    get_arbitrage_opportunity_detail,
    get_arbitrage_top,
    scan_arbitrage_session,
)

theme_apply_global: Optional[Callable[[], None]]
theme_render_header: Optional[Callable[[str, str], None]]

try:
    from ui.theme import apply_global_theme as theme_apply_global, render_app_header as theme_render_header
except ImportError:  # pragma: no cover - optional theming
    theme_apply_global = None
    theme_render_header = None

apply_global_theme: Optional[Callable[[], None]] = theme_apply_global
render_app_header: Optional[Callable[[str, str], None]] = theme_render_header


DEFAULT_QUOTES = [
    {"symbol": "ES", "venue": "EX_A", "ccy": "USD", "bid": 4998.0, "ask": 4999.0},
    {"symbol": "ES", "venue": "EX_B", "ccy": "USD", "bid": 5001.0, "ask": 5002.0},
]


def _init_session_state() -> None:
    st.session_state.setdefault("arb_session_id", None)
    st.session_state.setdefault("arb_quotes", DEFAULT_QUOTES)
    st.session_state.setdefault("arb_fx_rate", 3.5)
    st.session_state.setdefault("arb_min_edge_bps", 10.0)
    st.session_state.setdefault("arb_max_spread_bps", 15.0)
    st.session_state.setdefault("arb_max_age_ms", 5_000)
    st.session_state.setdefault("arb_max_notional", 50_000.0)
    st.session_state.setdefault("arb_max_qty", 1.0)


def _execution_constraints_from_state() -> Dict[str, float | int]:
    return {
        "min_edge_bps": st.session_state.get("arb_min_edge_bps"),
        "max_spread_bps": st.session_state.get("arb_max_spread_bps"),
        "max_age_ms": st.session_state.get("arb_max_age_ms"),
        "max_notional": st.session_state.get("arb_max_notional"),
        "max_qty": st.session_state.get("arb_max_qty"),
    }


def _render_header() -> None:
    if apply_global_theme is not None:
        apply_global_theme()
    if render_app_header is not None:
        render_app_header("Arbitrage Monitor", "")


def main() -> None:  # pragma: no cover - Streamlit UI
    _init_session_state()
    _render_header()

    st.title("Arbitrage Monitor – ניטור הזדמנויות בין-בורסאיות")

    st.sidebar.header("Execution constraints")
    st.session_state["arb_min_edge_bps"] = st.sidebar.number_input(
        "Minimum edge (bps)", value=float(st.session_state["arb_min_edge_bps"]), step=0.5
    )
    st.session_state["arb_max_spread_bps"] = st.sidebar.number_input(
        "Max spread (bps)", value=float(st.session_state["arb_max_spread_bps"]), step=1.0
    )
    st.session_state["arb_max_age_ms"] = st.sidebar.number_input(
        "Max quote age (ms)", value=int(st.session_state["arb_max_age_ms"]), step=100
    )
    st.session_state["arb_max_notional"] = st.sidebar.number_input(
        "Max notional", value=float(st.session_state["arb_max_notional"]), step=1_000.0, format="%.2f"
    )
    st.session_state["arb_max_qty"] = st.sidebar.number_input(
        "Max quantity", value=float(st.session_state["arb_max_qty"]), step=0.1
    )

    if st.button("צור Session חדש לארביטראז'"):
        try:
            session_id = create_arbitrage_session()
            st.session_state["arb_session_id"] = session_id
            st.success(f"Session חדש נוצר: {session_id}")
        except ApiError as exc:  # pragma: no cover - network
            st.error(f"שגיאה ביצירת Session: {exc}")

    session_id = st.session_state.get("arb_session_id")
    if not session_id:
        st.info("נא ליצור תחילה Session חדש כדי להתחיל לעקוב אחר הזדמנויות.")
        return

    st.write(f"Session ID פעיל: **{session_id}**")

    st.subheader("עריכת Quotes")
    edited_quotes = st.data_editor(
        st.session_state.get("arb_quotes", DEFAULT_QUOTES),
        num_rows="dynamic",
        key="arb_quotes",
    )

    st.session_state["arb_fx_rate"] = st.number_input(
        "USD/ILS FX rate", value=st.session_state.get("arb_fx_rate", 3.5), step=0.01, format="%.4f"
    )

    if st.button("סרוק הזדמנויות"):
        try:
            opportunities = scan_arbitrage_session(
                session_id=session_id,
                fx_rate_usd_ils=st.session_state["arb_fx_rate"],
                quotes=edited_quotes,
                constraints=_execution_constraints_from_state(),
            )
            if not opportunities:
                st.info("לא נמצאו הזדמנויות העומדות בסף המינימלי.")
            else:
                st.success(f"נמצאו {len(opportunities)} הזדמנויות.")
                st.dataframe(pd.DataFrame(opportunities))
        except ApiError as exc:  # pragma: no cover - network
            st.error(f"שגיאת API בעת הרצת סריקה: {exc}")

    st.subheader("היסטוריית הזדמנויות")
    try:
        history = get_arbitrage_history(session_id=session_id)
    except ApiError as exc:  # pragma: no cover - network
        st.error(f"שגיאה בהבאת היסטוריה: {exc}")
        history = []

    if history:
        df_hist = pd.DataFrame(history)
        df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"])
        st.dataframe(df_hist)
        if "edge_bps" in df_hist:
            chart_df = df_hist.set_index("timestamp")["edge_bps"]
            st.line_chart(chart_df)
    else:
        st.info("טרם נאספו הזדמנויות עבור Session זה.")

    st.subheader("Top Recommendations")
    try:
        recs = get_arbitrage_top(session_id=session_id, limit=10)
    except ApiError as exc:  # pragma: no cover - network
        st.error(f"שגיאת API בעת הבאת המלצות: {exc}")
        recs = []

    if recs:
        df_recs = pd.DataFrame(recs)
        core_cols = ["rank", "opportunity_id", "quality_score"]
        hidden_cols = {"rank", "opportunity_id", "quality_score", "reasons", "signals", "economics"}
        extra_cols = [col for col in df_recs.columns if col not in hidden_cols]
        st.dataframe(df_recs[core_cols + extra_cols])
        selected = st.selectbox(
            "בחר Opportunity להצגת פרטים",
            options=[r["opportunity_id"] for r in recs],
            index=0,
        )
        if selected:
            detail = get_arbitrage_opportunity_detail(
                session_id=session_id,
                opportunity_id=selected,
                constraints=_execution_constraints_from_state(),
            )
            st.write("Lifecycle state:", detail.get("state"))
            readiness = detail.get("execution") or detail.get("execution_readiness") or {}
            decision = detail.get("execution_decision") or readiness.get("decision") or {}

            can_execute = decision.get("can_execute")
            if can_execute is None:
                can_execute = bool(
                    readiness.get("can_execute")
                    or readiness.get("should_execute")
                    or readiness.get("executable")
                    or readiness.get("is_executable")
                )

            badge_color = "#16a34a" if can_execute else "#b91c1c"
            badge_label = "EXECUTABLE" if can_execute else "BLOCKED"
            st.markdown(
                f"<div style='display:inline-block;padding:0.25rem 0.75rem;border-radius:999px;"
                f"background:{badge_color};color:white;font-weight:700;'>{badge_label}</div>",
                unsafe_allow_html=True,
            )

            reasons = (
                decision.get("reason_codes")
                or readiness.get("reason_codes")
                or readiness.get("reasons")
                or []
            )
            if reasons and not can_execute:
                st.info(f"Primary block reason: {reasons[0]}")

            metrics: Dict[str, Any] = {}
            metrics.update(decision.get("metrics", {}))
            metrics.update(readiness.get("metrics", {}))
            for key in ["edge_bps", "spread_bps", "worst_spread_bps", "age_ms", "notional"]:
                if key in readiness:
                    metrics.setdefault(key, readiness.get(key))
                if key in decision:
                    metrics.setdefault(key, decision.get(key))

            recommended_qty = decision.get("recommended_qty") or readiness.get("recommended_qty")
            if recommended_qty is not None:
                metrics.setdefault("recommended_qty", recommended_qty)

            if metrics:
                cols = st.columns(min(3, len(metrics)))
                for idx, (metric_name, metric_value) in enumerate(metrics.items()):
                    cols[idx % len(cols)].metric(metric_name.replace("_", " ").title(), f"{metric_value}")

            if reasons:
                st.write("Execution reasons:")
                st.write("\n".join(f"• {reason}" for reason in reasons))

            with st.expander("Execution details (advanced)", expanded=False):
                st.json(
                    {
                        "execution_decision": decision,
                        "execution_readiness": readiness,
                    }
                )
            st.write("Signals:")
            st.json(detail.get("signals", {}))
            st.write("Reasons:")
            st.json(detail.get("reasons", []))
    else:
        st.info("אין עדיין המלצות מדורגות ל-Session זה.")


if __name__ == "__main__":
    main()
