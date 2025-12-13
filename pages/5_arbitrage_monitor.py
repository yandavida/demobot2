from __future__ import annotations

import pandas as pd
import streamlit as st
from typing import Callable, Optional

from ui.api_client import (
    ApiError,
    create_arbitrage_session,
    get_arbitrage_history,
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


def _render_header() -> None:
    if apply_global_theme is not None:
        apply_global_theme()
    if render_app_header is not None:
        render_app_header("Arbitrage Monitor", "")


def main() -> None:  # pragma: no cover - Streamlit UI
    _init_session_state()
    _render_header()

    st.title("Arbitrage Monitor – ניטור הזדמנויות בין-בורסאיות")

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


if __name__ == "__main__":
    main()
