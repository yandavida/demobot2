# Layer: ui
# app.py
# -----------------------------------------
# Iron Condor – Options Desk (Simulator)
# -----------------------------------------

from datetime import date

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ערכת עיצוב + Header
from ui.theme import apply_global_theme, render_app_header

from core.strategy_metadata import get_strategy_comparison_rows

# שירות יצירת שרשרת
from services.chain_service import generate_chain

# סיידבר של שוק (Spot, r, q, iv, expiry)
from ui.controls_market import build_market_sidebar

# סיידבר בחירת אסטרטגיה
from ui.controls import build_strategy_sidebar

# רישום אסטרטגיות
from core.strategies_registry import get_strategies

# פילטרים וטבלאות
from core.core.utils.filters import df_basic_filter, apply_advanced_filters
from core.core.utils.pagination import paginate_df

# ויזואליזציה לשרשרת + סטייל לגרפים
from charts.chain_view import render_chain_visualization, style_figure


# ===== Page config =====
st.set_page_config(
    page_title="Options Desk (Simulator)",
    layout="wide",
)

# החלת ערכת עיצוב גלובלית
apply_global_theme()

# Header עליון
render_app_header(
    "Options Chain (Simulator)",
    "סימולטור עבודה לרצף אופציות – שרשרת, פילטרים ו־Iron Condor",
)


# ===== Helpers =====
def ensure_odd(n: int) -> int:
    """אם קיבלנו מספר זוגי – נהפוך אותו לאי־זוגי (למעלה)."""
    return n if n % 2 == 1 else n + 1


# ===== Sidebar – inputs (עכשיו דרך controls_market.py ו-controls.py) =====
spot, r, q, iv, expiry = build_market_sidebar()

strategies = get_strategies()
chosen = build_strategy_sidebar(strategies, key_prefix="main")

# ===== Sidebar – chain parameters =====
st.sidebar.header("Chain parameters")

strikes_count = st.sidebar.slider(
    "Strikes count (odd only)",
    min_value=5,
    max_value=99,
    value=9,
    step=2,  # רק אי-זוגיים
    help="בחרי מספר אי־זוגי של סטרייקים סביב הספוט.",
)

step_pct = st.sidebar.slider(
    "Strike step (% of spot)",
    min_value=0.5,
    max_value=10.0,
    value=2.0,
    step=0.5,
    help="מרחק בין סטרייקים כאחוז מהספוט (למשל 2.0 = כל ~2%).",
)


# ===== Main UI =====
st.title("Options Chain (Simulator)")

st.info(
    "ליצירת שרשרת אופציות סינתטית לפי הפרמטרים שבסיידבר, לחצי על **Generate chain**.\n\n"
    "התוצאה תוצג מטה עם פילטרים, דפדוף, גרפים וכפתורי הורדה.",
    icon="ℹ️",
)

# Session state
if "raw_chain" not in st.session_state:
    st.session_state["raw_chain"] = None
if "page_index" not in st.session_state:
    st.session_state["page_index"] = 0  # 0-based

col_btn, _ = st.columns([1, 6])
with col_btn:
    generate = st.button("Generate chain", type="primary")

if generate:
    try:
        sc = ensure_odd(int(strikes_count))  # לוודא אי-זוגי

        # שימוש בשכבת השירות החדשה
        chain = generate_chain(
            symbol="TA35",
            expiry=expiry,
            spot=spot,
            r=r,
            q=q,
            iv=iv,
            strikes_count=sc,
            step_pct=step_pct,
        )

        st.session_state["raw_chain"] = chain.copy()
        st.session_state["page_index"] = 0  # תמיד חוזרים לעמוד הראשון
        st.success("Chain generated")

    except Exception as e:
        st.session_state["raw_chain"] = None
        st.error(f"{type(e).__name__}: {e}")


# ===== Results + Filters + Pagination =====
if st.session_state.get("raw_chain") is not None:
    df = st.session_state["raw_chain"].copy()

    st.subheader("Filters")

    # פילטר לפי סוג אופציה
    cp_sel = st.multiselect(
        "Type (CALL/PUT)",
        options=sorted(df["cp"].unique().tolist()),
        default=sorted(df["cp"].unique().tolist()),
        help="סינון לפי סוג האופציה (CALL / PUT).",
        key="flt_cp",
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
        key="flt_strike",
    )

    # ===== Advanced filters =====
    with st.expander("Advanced filters (price & Greeks)", expanded=False):
        # תחומים דינמיים לכל עמודה
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
            key="flt_price",
        )
        delta_range = st.slider(
            "Delta range",
            min_value=d_lo,
            max_value=d_hi,
            value=(d_lo, d_hi),
            step=max((d_hi - d_lo) / 100, 1e-6),
            key="flt_delta",
        )
        gamma_range = st.slider(
            "Gamma range",
            min_value=g_lo,
            max_value=g_hi,
            value=(g_lo, g_hi),
            step=max((g_hi - g_lo) / 100, 1e-6),
            key="flt_gamma",
        )
        theta_range = st.slider(
            "Theta range",
            min_value=t_lo,
            max_value=t_hi,
            value=(t_lo, t_hi),
            step=max((t_hi - t_lo) / 100, 1e-6),
            key="flt_theta",
        )
        vega_range = st.slider(
            "Vega range",
            min_value=v_lo,
            max_value=v_hi,
            value=(v_lo, v_hi),
            step=max((v_hi - v_lo) / 100, 1e-6),
            key="flt_vega",
        )
        rho_range = st.slider(
            "Rho range",
            min_value=r_lo,
            max_value=r_hi,
            value=(r_lo, r_hi),
            step=max((r_hi - r_lo) / 100, 1e-6),
            key="flt_rho",
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

    # ---- Pagination Controls ----
    st.divider()
    st.subheader("Table")

    col_ps, col_pi, col_nav = st.columns([1, 1, 2], vertical_alignment="center")

    with col_ps:
        page_size = st.selectbox(
            "Rows per page",
            options=[10, 25, 50, 100],
            index=1,
            help="כמות שורות בעמוד.",
            key="rows_per_page",
        )

    # חישוב עמודים
    page_df, total_pages = paginate_df(
        df_view, page_size, st.session_state["page_index"]
    )

    with col_pi:
        current_page_one_based = st.number_input(
            "Page",
            min_value=1,
            max_value=max(1, total_pages),
            value=min(max(1, st.session_state["page_index"] + 1), max(1, total_pages)),
            step=1,
            help="מספר עמוד (1-based).",
            key="page_number_input",
        )
        st.session_state["page_index"] = current_page_one_based - 1  # החזרה ל-0-based

    with col_nav:
        c1, c2, c3 = st.columns([1, 1, 6])
        with c1:
            if st.button(
                "Prev", disabled=(st.session_state["page_index"] <= 0), key="btn_prev"
            ):
                st.session_state["page_index"] = max(
                    0, st.session_state["page_index"] - 1
                )
        with c2:
            if st.button(
                "Next",
                disabled=(
                    total_pages == 0
                    or st.session_state["page_index"] >= total_pages - 1
                ),
                key="btn_next",
            ):
                st.session_state["page_index"] = min(
                    total_pages - 1, st.session_state["page_index"] + 1
                )

        st.caption(
            f"עמוד **{st.session_state['page_index'] + 1}** מתוך **{max(1, total_pages)}**"
        )

    st.divider()

    # הורדות
    csv_all = df_view.to_csv(index=False).encode("utf-8")
    csv_page = page_df.to_csv(index=False).encode("utf-8")

    col_dl1, col_dl2 = st.columns([1, 1])
    with col_dl1:
        st.download_button(
            label="Download CSV (filtered all)",
            data=csv_all,
            file_name=f"options_chain_all_{date.today().isoformat()}.csv",
            mime="text/csv",
            help="הורדת כל התוצאות לאחר פילטרים.",
            key="dl_all",
        )
    with col_dl2:
        st.download_button(
            label="Download CSV (this page)",
            data=csv_page,
            file_name=(
                f"options_chain_page_{st.session_state['page_index'] + 1}_"
                f"{date.today().isoformat()}.csv"
            ),
            mime="text/csv",
            help="הורדת הנתונים של העמוד הנוכחי בלבד.",
            key="dl_page",
        )

    # טבלה – מציגים את הדף הנוכחי בלבד
    st.dataframe(page_df, use_container_width=True)

    # ===== Strategy playground (על בסיס df_view) =====
    st.divider()
    st.subheader("Strategy playground")

    strategies = get_strategies()
    chosen = build_strategy_sidebar(strategies, key_prefix="playground")

    if chosen is not None:
        if len(df_view) == 0:
            st.warning("אין נתונים להצגת אסטרטגיה אחרי הסינון.")
        else:
            chosen.render(df_view)

    # === Strategy comparison (qualitative table + chart) ===
    with st.expander("📊 Strategy comparison table", expanded=False):
        rows = get_strategy_comparison_rows()
        comp_df = pd.DataFrame(rows)

        # טבלה מלאה
        st.dataframe(comp_df, use_container_width=True)

        st.markdown("#### Position type distribution")

        # כמה אסטרטגיות מכל סוג: Credit / Debit / וכו'
        pos_counts = comp_df["Position type"].value_counts().reset_index()
        pos_counts.columns = ["Position type", "Count"]

        # גרף עמודות עם Plotly + style_figure כדי שלא יהיה מכווץ
        fig_bar = px.bar(
            pos_counts,
            x="Position type",
            y="Count",
        )
        fig_bar = style_figure(
            fig_bar,
            x_title="Position type",
            y_title="Count",
            title="Position type distribution",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # === Visualization ===
    with st.expander("📈 Visualization", expanded=False):
        render_chain_visualization(df_view)
