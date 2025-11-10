# app.py
# -----------------------------------------
# Iron Condor – Options Desk (Simulator)
# -----------------------------------------

from __future__ import annotations

from datetime import date, timedelta
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

# ברוקרים
from brokers import get_broker

# ===== Page config =====
st.set_page_config(
    page_title="Options Desk (Simulator)",
    layout="wide",
)

# ===== Helpers =====
def ensure_odd(n: int) -> int:
    """אם קיבלנו מספר זוגי – נהפוך אותו לאי־זוגי (למעלה)."""
    return n if n % 2 == 1 else n + 1


def df_basic_filter(
    df: pd.DataFrame,
    strikes_range: tuple[float, float],
    cp_sel: list[str],
) -> pd.DataFrame:
    lo, hi = strikes_range
    mask_strike = (df["strike"] >= lo) & (df["strike"] <= hi)
    mask_cp = df["cp"].isin(cp_sel) if cp_sel else True
    return df.loc[mask_strike & mask_cp].reset_index(drop=True)


def apply_advanced_filters(
    df: pd.DataFrame,
    price_range: tuple[float, float] | None,
    delta_range: tuple[float, float] | None,
    gamma_range: tuple[float, float] | None,
    theta_range: tuple[float, float] | None,
    vega_range: tuple[float, float] | None,
    rho_range: tuple[float, float] | None,
) -> pd.DataFrame:
    out = df.copy()
    if price_range:
        out = out[(out["price"] >= price_range[0]) & (out["price"] <= price_range[1])]
    if delta_range:
        out = out[(out["delta"] >= delta_range[0]) & (out["delta"] <= delta_range[1])]
    if gamma_range:
        out = out[(out["gamma"] >= gamma_range[0]) & (out["gamma"] <= gamma_range[1])]
    if theta_range:
        out = out[(out["theta"] >= theta_range[0]) & (out["theta"] <= theta_range[1])]
    if vega_range:
        out = out[(out["vega"] >= vega_range[0]) & (out["vega"] <= vega_range[1])]
    if rho_range:
        out = out[(out["rho"]  >= rho_range[0])  & (out["rho"]  <= rho_range[1])]
    return out.reset_index(drop=True)


def paginate_df(
    df: pd.DataFrame, page_size: int, page_index: int
) -> tuple[pd.DataFrame, int]:
    """
    מחזיר (דאטה של הדף, סך כל הדפים) לפי page_size ו-page_index (0-based).
    """
    total = len(df)
    if total == 0:
        return df, 0
    total_pages = int(np.ceil(total / page_size))
    page_index = max(0, min(page_index, total_pages - 1))
    start = page_index * page_size
    end = start + page_size
    return df.iloc[start:end].reset_index(drop=True), total_pages


# ===== Sidebar – market inputs =====
st.sidebar.header("Market")

spot = st.sidebar.number_input(
    "Spot (S)",
    min_value=0.0,
    value=3317.09,
    step=0.01,
    help="מחיר נכס הבסיס (ספוט) לעדכון החישובים.",
)

r = st.sidebar.number_input(
    "Risk-free r (annual, dec)",
    min_value=0.0,
    value=0.020,
    step=0.001,
    format="%.3f",
    help="ריבית חסרת סיכון שנתית (מספר עשרוני, למשל 0.02 = 2%).",
)

q = st.sidebar.number_input(
    "Dividend q (annual, dec)",
    min_value=0.0,
    value=0.000,
    step=0.001,
    format="%.3f",
    help="תשואת דיבידנד שנתית (מספר עשרוני).",
)

iv = st.sidebar.number_input(
    "IV (annual, dec)",
    min_value=0.01,
    value=0.18,
    step=0.01,
    format="%.2f",
    help="סטיית תקן מרומזת (Implied Vol).",
)

expiry = st.sidebar.date_input(
    "Expiry",
    value=date.today() + timedelta(days=30),
    help="מועד פקיעה של הסדרה.",
)

# ===== Sidebar – chain parameters =====
st.sidebar.header("Chain parameters")

# מחייב אי-זוגי באמצעות step=2
strikes_count = st.sidebar.slider(
    "Strikes count (odd only)",
    min_value=5,
    max_value=99,
    value=9,
    step=2,  # מאפשר רק אי־זוגיים
    help="בחרי מספר אי־זוגי כדי לקבל מרכז סביב הספוט.",
)

step_pct = st.sidebar.slider(
    "Strike step (% of spot)",
    min_value=0.5,
    max_value=10.0,
    value=2.0,
    step=0.5,
    help="מרחק בין סטרייקים כאחוז מהספוט (לדוגמה 2.0 = כל ~2%).",
)

st.sidebar.header("Broker")
broker_name = st.sidebar.selectbox(
    "Broker",
    options=["sim"],  # לעתיד נוסיף "ibkr" וכו'
    index=0,
    help="ברירת מחדל: סימולטור. בהמשך ניתן להחליף לברוקר אמיתי (IBKR).",
)

broker = get_broker(broker_name)

# ודא חיבור
if not broker.is_connected():
    broker.connect()

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
        sc = ensure_odd(int(strikes_count))  # ביטוח אי-זוגי

        chain = broker.get_option_chain(
            symbol="TA35",
            expiry=expiry,
            spot=spot,
            r=r,
            q=q,
            iv=iv,
            strikes_count=sc,    # חובה אי-זוגי (מרכז סביב ספוט)
            step_pct=step_pct,   # מרחק בין סטרייקים כאחוז מהספוט
        )

        if not isinstance(chain, pd.DataFrame) or chain.empty:
            raise ValueError("השרשרת ריקה או בפורמט לא צפוי.")

        st.session_state["raw_chain"] = chain.copy()
        st.session_state["page_index"] = 0  # אתחול דף ראשון
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

        price_range = st.slider("Price range", min_value=p_lo, max_value=p_hi,
                                value=(p_lo, p_hi), step=(p_hi - p_lo) / 100, key="flt_price")
        delta_range = st.slider("Delta range", min_value=d_lo, max_value=d_hi,
                                value=(d_lo, d_hi), step=(d_hi - d_lo) / 100, key="flt_delta")
        gamma_range = st.slider("Gamma range", min_value=g_lo, max_value=g_hi,
                                value=(g_lo, g_hi), step=(g_hi - g_lo) / 100, key="flt_gamma")
        theta_range = st.slider("Theta range", min_value=t_lo, max_value=t_hi,
                                value=(t_lo, t_hi), step=(t_hi - t_lo) / 100, key="flt_theta")
        vega_range  = st.slider("Vega range",  min_value=v_lo, max_value=v_hi,
                                value=(v_lo, v_hi), step=(v_hi - v_lo) / 100, key="flt_vega")
        rho_range   = st.slider("Rho range",   min_value=r_lo, max_value=r_hi,
                                value=(r_lo, r_hi), step=(r_hi - r_lo) / 100, key="flt_rho")

    # החלת פילטרים
    df_view = df_basic_filter(df, strikes_range, cp_sel)
    df_view = apply_advanced_filters(
        df_view, price_range, delta_range, gamma_range, theta_range, vega_range, rho_range
    )

    st.caption(f"סה\"כ אחרי סינון: **{len(df_view):,}** רשומות")

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

    # חשב עמודים והגשה
    page_df, total_pages = paginate_df(
        df_view, page_size, st.session_state["page_index"]
    )

    with col_pi:
        current_page_one_based = st.number_input(
            "Page",
            min_value=1,
            max_value=max(1, total_pages),
            value=min(
                max(1, st.session_state["page_index"] + 1), max(1, total_pages)
            ),
            step=1,
            help="מספר עמוד (1-based).",
            key="page_number_input",
        )
        st.session_state["page_index"] = current_page_one_based - 1  # החזרה ל-0-based

    with col_nav:
        c1, c2, c3 = st.columns([1, 1, 6])
        with c1:
            if st.button("Prev", disabled=(st.session_state["page_index"] <= 0), key="btn_prev"):
                st.session_state["page_index"] = max(
                    0, st.session_state["page_index"] - 1
                )
        with c2:
            if st.button(
                "Next",
                disabled=(total_pages == 0 or st.session_state["page_index"] >= total_pages - 1),
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
            file_name=f"options_chain_page_{st.session_state['page_index'] + 1}_{date.today().isoformat()}.csv",
            mime="text/csv",
            help="הורדת הנתונים של העמוד הנוכחי בלבד.",
            key="dl_page",
        )

    # טבלה – מציגים את הדף הנוכחי בלבד
    st.dataframe(page_df, width="stretch")

    # === Strategy Sandbox: Iron Condor ===
    with st.expander("🧪 Strategy: Iron Condor (quick sandbox)", expanded=False):
        if len(df_view) == 0:
            st.warning("אין נתונים להצגה לאחר הסינון הנוכחי.")
        else:
            # בוחרים סטרייקים מתוך הדאטה המסוננת
            puts  = df_view[df_view["cp"] == "PUT"].sort_values("strike")
            calls = df_view[df_view["cp"] == "CALL"].sort_values("strike")

            colA, colB, colC, colD = st.columns(4)
            with colA:
                sp = st.selectbox("Short PUT strike",  puts["strike"].unique().tolist(), key="ic_sp")
            with colB:
                lp = st.selectbox("Long  PUT strike",  puts["strike"].unique().tolist(), key="ic_lp")
            with colC:
                sc = st.selectbox("Short CALL strike", calls["strike"].unique().tolist(), key="ic_sc")
            with colD:
                lc = st.selectbox("Long  CALL strike", calls["strike"].unique().tolist(), key="ic_lc")

            qty = st.number_input("Quantity (contracts)", min_value=1, value=1, step=1, key="ic_qty")
            mult = st.number_input("Contract multiplier", min_value=1, value=100, step=1, key="ic_mult")

            # משיכת מחירי אופציות לפי סטרייקים
            def mid_price(df_, k, cp):
                row = df_[(df_["strike"] == k) & (df_["cp"] == cp)]
                return float(row["price"].iloc[0]) if not row.empty else np.nan

            price_sp = mid_price(df_view, sp, "PUT")   # אנחנו מוכרים => קרדיט
            price_lp = mid_price(df_view, lp, "PUT")   # אנחנו קונים  => דביט
            price_sc = mid_price(df_view, sc, "CALL")  # אנחנו מוכרים => קרדיט
            price_lc = mid_price(df_view, lc, "CALL")  # אנחנו קונים  => דביט

            if np.isnan([price_sp, price_lp, price_sc, price_lc]).any():
                st.error("לא נמצאו מחירים לכל הסטרייקים שנבחרו. בדקי שהסטרייקים קיימים בפילטר הנוכחי.")
            else:
                # בדיקות היגיון בסיסיות (כנפיים)
                wing_put  = abs(sp - lp)
                wing_call = abs(lc - sc)
                net_credit = (price_sp + price_sc) - (price_lp + price_lc)

                max_loss_per_unit = max(wing_put, wing_call) - net_credit
                max_profit_per_unit = net_credit
                lower_be = sp - net_credit
                upper_be = sc + net_credit

                # סכומים כוללים
                gross_max_profit = max_profit_per_unit * qty * mult
                gross_max_loss   = max_loss_per_unit   * qty * mult

                m1, m2, m3 = st.columns(3)
                m1.metric("Max Profit (credit)", f"{gross_max_profit:,.2f}")
                m2.metric("Max Loss (worst wing − credit)", f"{gross_max_loss:,.2f}")
                m3.metric("Credit per unit", f"{net_credit:,.4f}")

                st.caption(f"Break-even points: **{lower_be:.2f}** / **{upper_be:.2f}**")

                # גרף Payoff ביום פקיעה
                s_min = min(lp, sp, sc, lc, spot) * 0.9
                s_max = max(lp, sp, sc, lc, spot) * 1.1
                S = np.linspace(s_min, s_max, 300)

                def payoff_put(k, price, short=True):
                    # תשלום ליחידה (ללא מכפיל) – ערך בזמן פקיעה פחות פרמיה
                    intrinsic = np.maximum(k - S, 0.0)
                    return (price - intrinsic) if short else (intrinsic - price)

                def payoff_call(k, price, short=True):
                    intrinsic = np.maximum(S - k, 0.0)
                    return (price - intrinsic) if short else (intrinsic - price)

                pl = (
                    payoff_put(sp, price_sp, short=True)   # short put
                    + payoff_put(lp, price_lp, short=False) # long put
                    + payoff_call(sc, price_sc, short=True) # short call
                    + payoff_call(lc, price_lc, short=False)# long call
                ) * qty * mult

                df_pay = pd.DataFrame({"S": S, "P/L": pl})
                fig_pay = px.line(df_pay, x="S", y="P/L", title="Iron Condor payoff (expiry)")
                fig_pay.add_vline(x=lower_be, line_dash="dash", line_color="orange")
                fig_pay.add_vline(x=upper_be, line_dash="dash", line_color="orange")
                fig_pay.add_vline(x=spot,     line_dash="dot",  line_color="gray")
                st.plotly_chart(fig_pay, use_container_width=True, key="ic_payoff")

    # === Chart / Visualization (על בסיס df_view) ===
    with st.expander("📈 Visualization", expanded=True):
        st.caption("אפשר לבחור מדד (מחיר/דלתא/וגה וכו') וסוג גרף, על בסיס התוצאות לאחר סינון.")
        df_chart_src = df_view.copy()

        chart_metric = st.selectbox(
            "בחרי מדד להצגה",
            ["price", "delta", "gamma", "theta", "vega", "rho"],
            key="metric_select_v1",
        )
        chart_type = st.radio(
            "Chart type",
            options=["Line", "Scatter", "Histogram"],
            index=0,
            horizontal=True,
            key="chart_type_v1",
        )

        if len(df_chart_src) == 0:
            st.warning("אין נתונים להצגה לאחר הסינון הנוכחי.")
        else:
            if chart_type == "Line":
                fig = px.line(
                    df_chart_src.sort_values("strike"),
                    x="strike", y=chart_metric, color="cp",
                    title=f"Line: {chart_metric} vs strike",
                    markers=True,
                )
            elif chart_type == "Scatter":
                fig = px.scatter(
                    df_chart_src,
                    x="strike", y=chart_metric, color="cp",
                    title=f"Scatter: {chart_metric} vs strike",
                    trendline="lowess",
                )
            else:  # Histogram
                fig = px.histogram(
                    df_chart_src,
                    x=chart_metric, color="cp", barmode="overlay",
                    nbins=40, opacity=0.6,
                    title=f"Histogram: {chart_metric}",
                )

            st.plotly_chart(fig, use_container_width=True, key="options_chart_v1")

# ===== Footer / Notes =====
with st.expander("הערות ומידע"):
    st.markdown(
        """
- **מקור הנתונים**: סימולטור (`sim`) המייצר שרשרת אופציות מחושבת (Black–Scholes).
- **אי-זוגיות סטרייקים**: השרשרת נבנית סביב מרכז (ATM). לכן אנו דורשים מספר סטרייקים אי-זוגי כדי לאפשר סימטריה סביב הספוט.
- **Pagination**: בחרי גודל עמוד, עברי עמודים עם Prev/Next או הזיני מספר עמוד ידנית.
- **Strategy Sandbox**: בחירה ידנית של סטרייקים מייצרת חישוב **קרדיט**, **רווח/הפסד מקסימלי** ונקודות **Break-even** + גרף Payoff.
- **המשך פיתוח**: שילוב IBKR (TWS API) לנתוני שוק חיים, Greeks/PNL דינמיים והזרמה בזמן אמת.
        """
    )
