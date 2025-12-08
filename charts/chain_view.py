# charts.py
import streamlit as st
import plotly.express as px
import pandas as pd


# ============================================================
#   פונקציה לעיצוב גרפים – פתרון גורף לבעיית הגובה/תצוגה
# ============================================================
def style_figure(
    fig,
    *,
    height: int = 420,
    x_title: str = "",
    y_title: str = "",
    title: str = "",
):
    """
    עיצוב גרפים כדי שייראו טוב עם ערכת הצבעים החדשה.
    משתמשים בזה בכל הדפים, גם בגרפים קיימים וגם בחדשים.
    """
    fig.update_layout(
        height=height,
        title=title,
        margin=dict(l=60, r=40, t=60, b=60),
        xaxis_title=x_title,
        yaxis_title=y_title,
    )
    return fig


# ============================================================
#   גרף השרשרת הקיים – עם תיקון תצוגה
# ============================================================
def render_chain_visualization(df_view):
    """מציג גרפים על בסיס df_view אחרי סינון."""
    df_chart_src = df_view.copy() if df_view is not None else pd.DataFrame()

    if df_chart_src.empty:
        st.warning("אין נתונים להצגה לאחר הסינון.")
        return

    chart_metric = st.selectbox(
        "בחרי מדד להצגה",
        ["price", "delta", "gamma", "theta", "vega", "rho"],
        key="metric_select_v1",
    )

    chart_type = st.radio(
        "Chart type",
        ["Line", "Scatter", "Histogram"],
        horizontal=True,
        key="chart_type_v1",
    )

    # ============================
    # גרפים שונים לפי סוג
    # ============================
    if chart_type == "Line":
        fig = px.line(
            df_chart_src.sort_values("strike"),
            x="strike",
            y=chart_metric,
            color="cp",
            labels={"strike": "Strike", chart_metric: chart_metric},
        )
        fig = style_figure(fig, x_title="Strike", y_title=chart_metric)

    elif chart_type == "Scatter":
        fig = px.scatter(
            df_chart_src,
            x="strike",
            y=chart_metric,
            color="cp",
            trendline="lowess",
            labels={"strike": "Strike", chart_metric: chart_metric},
        )
        fig = style_figure(fig, x_title="Strike", y_title=chart_metric)

    else:  # Histogram
        fig = px.histogram(
            df_chart_src,
            x=chart_metric,
            color="cp",
            nbins=40,
            opacity=0.6,
            labels={chart_metric: chart_metric},
        )
        fig = style_figure(fig, x_title=chart_metric, y_title="Count")

    # ============================
    # הצגת הגרף
    # ============================
    st.plotly_chart(fig, use_container_width=True)
