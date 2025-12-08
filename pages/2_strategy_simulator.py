# Layer: ui
# pages/2_strategy_simulator.py
# -----------------------------------------
# Strategy Simulator – SaaS-first (עם fallback ל-local chain_service)
# -----------------------------------------

from __future__ import annotations

from datetime import date
from typing import Tuple

import numpy as np
import pandas as pd
import streamlit as st

# חישוב מקומי – fallback אם ה-API לא קיים / נכשל
from services.chain_service import generate_chain as generate_chain_local

from ui.controls_market import build_market_sidebar
from core.core.utils.filters import df_basic_filter, apply_advanced_filters
from core.core.utils.pagination import paginate_df
from charts.chain_view import render_chain_visualization
from core.strategies_registry import get_strategies
from ui.controls import build_strategy_sidebar
from ui.theme import apply_global_theme
from ui.api_client import generate_chain_v1  # SaaS chain generator wrapper


# ===== Page config & theme =====

st.set_page_config(
    page_title="Options Strategies – Simulator",
    layout="wide",
)

apply_global_theme()


# ===== Session keys =====

CHAIN_STATE_KEY = "strategy_raw_chain"
PAGE_INDEX_KEY = "strategy_page_index"

if CHAIN_STATE_KEY not in st.session_state:
    st.session_state[CHAIN_STATE_KEY] = None
if PAGE_INDEX_KEY not in st.session_state:
    st.session_state[PAGE_INDEX_KEY] = 0


# ===== Helper – SaaS-first chain generation =====


def get_chain_for_strategies(
    symbol: str,
    expiry: date,
    spot: float,
    r: float,
    q: float,
    iv: float,
    strikes_count: int,
    step_pct: float,
) -> Tuple[pd.DataFrame, str]:
    """
    מנסה קודם לייצר שרשרת דרך ה-SaaS API (generate_chain_v1).
    אם ה-API לא קיים / מחזיר שגיאה – נופלים לשרת המקומי (generate_chain_local).

    מחזיר:
        (DataFrame של שרשרת, מקור הנתונים: "api" או "local").
    """
    # ניסיון ראשון – SaaS API
    try:
        df_api = generate_chain_v1(
            symbol=symbol,
            expiry=expiry,
            spot=spot,
            r=r,
            q=q,
            iv=iv,
            strikes_count=strikes_count,
            step_pct=step_pct,
        )
        return df_api, "api"
    except Exception as api_err:
        # לא מפיל את ה-UI – רק מודיע שנעבור לחישוב מקומי
        st.info(
            "קריאה ל-SaaS API ליצירת שרשרת נכשלה, עוברים לחישוב מקומי. "
            f"(פרטי שגיאה: {type(api_err).__name__})"
        )

    # ניסיון שני – החישוב המקומי הקיים
    df_local = generate_chain_local(
        symbol=symbol,
        expiry=expiry,
        spot=spot,
        r=r,
        q=q,
        iv=iv,
        strikes_count=strikes_count,
        step_pct=step_pct,
    )
    return df_local, "local"


# ===== Sidebar – Market & Chain inputs =====

with st.sidebar:
    st.header("Market inputs")

    # בחירת סימבול בנפרד (לא מגיע מ-build_market_sidebar)
    symbol = st.text_input(
        "Underlying symbol (Ticker)",
        value="SPY",
        key="sim_symbol",
    )

    # הפונקציה מחזירה 5 ערכים: spot, r, q, iv, expiry
    spot, r, q, iv, expiry = build_market_sidebar()

    st.header("Chain parameters")
    strikes_count = st.slider(
        "Strikes count (odd only)",
        min_value=5,
        max_value=99,
        value=9,
        step=2,  # רק אי־זוגיים
        help="מספר סטרייקים סביב הספוט (חייב להיות אי־זוגי).",
        key="sim_strikes_count",
    )

    step_pct = st.slider(
        "Strike step (% of spot)",
        min_value=0.5,
        max_value=10.0,
        value=2.0,
        step=0.5,
        help="מרחק בין סטרייקים כאחוז מהספוט (למשל 2.0 = כל ~2%).",
        key="sim_step_pct",
    )


# ===== Main UI =====

st.title("Strategy Simulator")

st.info(
    "דף זה מיועד להרצת אסטרטגיות (כמו Iron Condor) על גבי שרשרת האופציות. "
    "תחילה מייצרים שרשרת אופציות, לאחר מכן בוחרים אסטרטגיה ומריצים סימולטור.",
    icon="ℹ️",
)

col_btn, _ = st.columns([1, 6])
with col_btn:
    generate = st.button(
        "Generate chain (SaaS-first, fallback to local)",
        type="primary",
    )

# יצירת שרשרת – שמירה ל-session_state
if generate:
    with st.spinner("יוצר שרשרת אופציות לחישובי אסטרטגיות..."):
        try:
            chain_df, source = get_chain_for_strategies(
                symbol=symbol,
                expiry=expiry,
                spot=spot,
                r=r,
                q=q,
                iv=iv,
                strikes_count=strikes_count,
                step_pct=step_pct,
            )
        except Exception as e:
            st.error(f"שגיאה ביצירת שרשרת אופציות: {e}")
        else:
            st.session_state[CHAIN_STATE_KEY] = chain_df
            st.success(f"שרשרת אופציות נוצרה בהצלחה (מקור: {source}).")


# ===== אם יש שרשרת – פילטרים, טבלה ואסטרטגיות =====

if st.session_state.get(CHAIN_STATE_KEY) is not None:
    df = st.session_state[CHAIN_STATE_KEY].copy()

    st.subheader("Filters")

    # פילטר לפי סוג אופציה
    cp_sel = st.multiselect(
        "Type (CALL/PUT)",
        options=sorted(df["cp"].unique().tolist()),
        default=sorted(df["cp"].unique().tolist()),
        help="סינון לפי סוג האופציה (CALL / PUT).",
        key="sim_flt_cp",
    )

    # פילטר לפי טווח סטרייק
    min_k, max_k = float(df["strike"].min()), float(df["strike"].max())
    strikes_range = st.slider(
        "Strike range",
        min_value=float(np.floor(min_k)),
        max_value=float(np.ceil(max_k)),
        value=(float(np.floor(min_k)), float(np.ceil(max_k))),
        step=1.0,
        help="בחרי טווח סטרייקים בסיסי לסינון.",
        key="sim_flt_strike",
    )

    # ===== Advanced filters =====
    with st.expander("Advanced filters (price & Greeks)", expanded=False):

        def rng(series: pd.Series, pad: float = 0.0):
            lo, hi = float(series.min()), float(series.max())
            if lo == hi:
                lo -= 1.0
                hi += 1.0
            span = hi - lo
            return lo - pad * span, hi + pad * span

        p_lo, p_hi = rng(df["price"])
        d_lo, d_hi = rng(df["delta"])
        g_lo, g_hi = rng(df["gamma"])
        t_lo, t_hi = rng(df["theta"])
        v_lo, v_hi = rng(df["vega"])
        r_lo, r_hi = rng(df["rho"])

        price_range = st.slider(
            "Price range",
            min_value=p_lo,
            max_value=p_hi,
            value=(p_lo, p_hi),
            step=max((p_hi - p_lo) / 100, 1e-6),
            key="sim_flt_price",
        )
        delta_range = st.slider(
            "Delta range",
            min_value=d_lo,
            max_value=d_hi,
            value=(d_lo, d_hi),
            step=max((d_hi - d_lo) / 100, 1e-6),
            key="sim_flt_delta",
        )
        gamma_range = st.slider(
            "Gamma range",
            min_value=g_lo,
            max_value=g_hi,
            value=(g_lo, g_hi),
            step=max((g_hi - g_lo) / 100, 1e-6),
            key="sim_flt_gamma",
        )
        theta_range = st.slider(
            "Theta range",
            min_value=t_lo,
            max_value=t_hi,
            value=(t_lo, t_hi),
            step=max((t_hi - t_lo) / 100, 1e-6),
            key="sim_flt_theta",
        )
        vega_range = st.slider(
            "Vega range",
            min_value=v_lo,
            max_value=v_hi,
            value=(v_lo, v_hi),
            step=max((v_hi - v_lo) / 100, 1e-6),
            key="sim_flt_vega",
        )
        rho_range = st.slider(
            "Rho range",
            min_value=r_lo,
            max_value=r_hi,
            value=(r_lo, r_hi),
            step=max((r_hi - r_lo) / 100, 1e-6),
            key="sim_flt_rho",
        )

    # החלת פילטרים
    df_view = df_basic_filter(df, strikes_range, cp_sel)
    df_view = apply_advanced_filters(
        df_view,
        price_range,
        delta_range,
        gamma_range,
        theta_range,
        vega_range,
        rho_range,
    )

    st.caption(f'סה"כ אחרי סינון: **{len(df_view):,}** רשומות')

    # ===== טבלה + פאג׳ינציה =====
    st.divider()
    st.subheader("Filtered chain – for strategies")

    col_ps, col_pi, col_nav = st.columns([1, 1, 2], vertical_alignment="center")

    with col_ps:
        page_size = st.selectbox(
            "Rows per page",
            options=[10, 25, 50, 100],
            index=1,
            help="כמות שורות בעמוד.",
            key="sim_rows_per_page",
        )

    page_df, total_pages = paginate_df(
        df_view, page_size, st.session_state[PAGE_INDEX_KEY]
    )

    with col_pi:
        current_page_one_based = st.number_input(
            "Page",
            min_value=1,
            max_value=max(1, total_pages),
            value=min(
                max(1, st.session_state[PAGE_INDEX_KEY] + 1), max(1, total_pages)
            ),
            step=1,
            help="מספר עמוד (1-based).",
            key="sim_page_number_input",
        )
        st.session_state[PAGE_INDEX_KEY] = current_page_one_based - 1

    with col_nav:
        c1, c2, c3 = st.columns([1, 1, 6])
        with c1:
            if st.button(
                "Prev",
                disabled=(st.session_state[PAGE_INDEX_KEY] <= 0),
                key="sim_btn_prev",
            ):
                st.session_state[PAGE_INDEX_KEY] = max(
                    0, st.session_state[PAGE_INDEX_KEY] - 1
                )
        with c2:
            if st.button(
                "Next",
                disabled=(
                    total_pages == 0
                    or st.session_state[PAGE_INDEX_KEY] >= total_pages - 1
                ),
                key="sim_btn_next",
            ):
                st.session_state[PAGE_INDEX_KEY] = min(
                    total_pages - 1, st.session_state[PAGE_INDEX_KEY] + 1
                )

        st.caption(
            f"עמוד **{st.session_state[PAGE_INDEX_KEY] + 1}** מתוך **{max(1, total_pages)}**"
        )

    st.dataframe(page_df, use_container_width=True)

    # ===== בחירת אסטרטגיה והרצה =====
    st.divider()
    st.subheader("Strategy playground")

    strategies = get_strategies()
    chosen = build_strategy_sidebar(strategies)

    if chosen is not None:
        if len(df_view) == 0:
            st.warning("אין נתונים להצגת אסטרטגיה אחרי הסינון.")
        else:
            chosen.render(df_view)

    # ===== Visualization על בסיס df_view =====
    with st.expander("📈 Visualization", expanded=False):
        render_chain_visualization(df_view)

else:
    st.warning(
        "כדי להריץ סימולטור אסטרטגיות, צריך קודם לייצר שרשרת אופציות (Generate chain)."
    )
