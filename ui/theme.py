# Layer: ui
# ui/theme.py
from __future__ import annotations
import streamlit as st


def apply_global_theme() -> None:
    """החלת ערכת צבעים ו־CSS גלובליים על כל האפליקציה."""
    st.markdown(
        """
        <style>
        :root {
            --bg-main: #262b35;          /* רקע ראשי – אפור כהה */
            --bg-main-light: #f5f5f5;
            --bg-sidebar: #22252f;       /* סיידבר */
            --bg-panel: #313644;         /* כרטיסים / פאנלים */
            --bg-panel-light: #ffffff;
            --accent: #f97316;           /* כתום */
            --accent-soft: #fbbf24;      /* כתום בהיר */
            --accent-alt: #22c55e;       /* ירוק */
            --danger: #ef4444;           /* אדום */
            --border-subtle: #3b4252;
            --text-main: #f9fafb;
            --text-soft: #e5e7eb;
            --text-muted: #9ca3af;
            --shadow-soft: 0 18px 45px rgba(0,0,0,0.35);
            --radius-lg: 18px;
        }

        /* רקע כללי */
        .stApp {
            background-color: var(--bg-main) !important;
        }

        /* אזור מרכזי */
        section.main > div {
            background-color: var(--bg-main) !important;
        }

        /* סיידבר */
        [data-testid="stSidebar"] {
            background-color: var(--bg-sidebar) !important;
            color: var(--text-main);
            border-right: 1px solid var(--border-subtle);
        }
        [data-testid="stSidebar"] * {
            color: var(--text-soft);
        }

        /* טקסט כללי + פונט */
        html, body, [class^="css"] {
            color: var(--text-main) !important;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        /* RTL לעברית */
        .stMarkdown p,
        .stMarkdown ul,
        .stMarkdown ol,
        .stMarkdown div,
        .stText,
        .stCaption,
        .stAlert p {
            direction: rtl;
            text-align: right;
        }
        .stMarkdown h1,
        .stMarkdown h2,
        .stMarkdown h3,
        .stMarkdown h4 {
            direction: rtl;
            text-align: right;
        }

        /* ===== Header עליון לאפליקציה ===== */
        .app-header {
            background: linear-gradient(90deg, #111827, #1f2937);
            padding: 1.1rem 1.5rem;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-soft);
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.5rem;
        }
        .app-header-left {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        .app-logo {
            width: 40px;
            height: 40px;
            border-radius: 999px;
            background: radial-gradient(circle at 30% 30%, #facc15, #f97316);
            display:flex;
            align-items:center;
            justify-content:center;
            font-size: 1.3rem;
            color:#111827;
            box-shadow: 0 8px 24px rgba(0,0,0,0.45);
        }
        .app-title-main {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent-soft);
        }
        .app-title-sub {
            font-size: 0.92rem;
            color: var(--text-muted);
        }
        .app-header-right {
            font-size: 0.85rem;
            color: var(--text-muted);
            text-align: left;
        }

        /* כותרות */
        h1, h2, h3, h4 {
            color: var(--accent) !important;
            letter-spacing: 0.03em;
        }

        /* ===== כפתורים ===== */
        .stButton > button,
        button[kind="primary"] {
            background: linear-gradient(135deg, var(--accent), var(--accent-soft)) !important;
            color: #111827 !important;
            border-radius: 999px !ינט!; 
            border: none !important;
            font-weight: 600 !important;
            padding: 0.5rem 1.2rem !important;
            box-shadow: 0 10px 25px rgba(249,115,22,0.45);
            transition: transform 0.08s ease-out, box-shadow 0.12s ease-out, filter 0.12s ease-out;
        }
        .stButton > button:hover,
        button[kind="primary"]:hover {
            filter: brightness(1.07);
            transform: translateY(-1px);
            box-shadow: 0 18px 35px rgba(249,115,22,0.55);
        }
        .stButton > button:active,
        button[kind="primary"]:active {
            transform: translateY(0px) scale(0.99);
            box-shadow: 0 6px 18px rgba(0,0,0,0.55);
        }

        /* כפתורים משניים */
        .stButton > button[kind="secondary"] {
            background: transparent !important;
            border: 1px solid var(--border-subtle) !important;
            color: var(--text-soft) !important;
            box-shadow: none !important;
        }

        /* תגים (ערכים ב-multiselect) */
        [data-baseweb="tag"] {
            background: rgba(249,115,22,0.12) !important;
            color: var(--accent-soft) !important;
            border-radius: 999px !important;
            border: 1px solid rgba(249,115,22,0.45) !important;
            font-weight: 500 !important;
        }

        /* ===== כרטיסים / קלטים / טבלאות ===== */
        [data-testid="stMetric"],
        .stAlert,
        .stDataFrame,
        .stTable,
        .stMultiSelect,
        .stSlider,
        .stSelectbox,
        .stTextInput,
        .stNumberInput {
            background-color: var(--bg-panel) !important;
            border-radius: var(--radius-lg) !important;
            border: 1px solid rgba(148,163,184,0.15) !important;
        }

        /* קלאס גנרי לכרטיסי הסבר */
        .app-card {
            background-color: var(--bg-panel);
            border-radius: var(--radius-lg);
            padding: 1rem 1.25rem;
            border: 1px solid rgba(148,163,184,0.18);
            box-shadow: 0 12px 30px rgba(0,0,0,0.35);
            margin-bottom: 1rem;
            transition: transform 0.08s ease-out, box-shadow 0.15s ease-out, border-color 0.15s ease-out;
        }
        .app-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 20px 45px rgba(0,0,0,0.5);
            border-color: rgba(249,115,22,0.45);
        }

        /* צ'יפים לרמת סיכון */
        .risk-chip {
            display:inline-flex;
            align-items:center;
            gap:0.35rem;
            padding:0.15rem 0.6rem;
            border-radius:999px;
            font-size:0.78rem;
            font-weight:500;
        }
        .risk-low {
            background: rgba(34,197,94,0.14);
            color:#bbf7d0;
            border:1px solid rgba(34,197,94,0.6);
        }
        .risk-medium {
            background: rgba(234,179,8,0.18);
            color:#facc15;
            border:1px solid rgba(234,179,8,0.7);
        }
        .risk-high {
            background: rgba(239,68,68,0.18);
            color:#fecaca;
            border:1px solid rgba(239,68,68,0.75);
        }

        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
           	background: #111827;
        }
        ::-webkit-scrollbar-thumb {
           	background: #4b5563;
           	border-radius: 999px;
        }
        ::-webkit-scrollbar-thumb:hover {
           	background: #6b7280;
        }

        /* ===== Plotly / Charts – בלי לרסק גובה ===== */
        /* הקונטיינר של הגרף – סגנון בלבד, בלי padding */
        .stPlotlyChart,
        .js-plotly-plot {
            border-radius: var(--radius-lg) !important;
            background-color: var(--bg-panel) !important;
            padding: 0 !important;      /* <-- כאן הפסקנו למעוך את הגרף */
        }

        /* הקופסאות הפנימיות של Plotly – גובה מינימלי סביר */
        .stPlotlyChart,
        .stPlotlyChart > div,
        .js-plotly-plot,
        .plot-container {
            height: auto !important;
            min-height: 380px !important;   /* אפשר לשנות לפי טעם */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_app_header(title: str, subtitle: str = "") -> None:
    """Header עליון אחיד לכל הדפים."""
    st.markdown(
        f"""
        <div class="app-header">
          <div class="app-header-left">
            <div class="app-logo">Δ</div>
            <div>
              <div class="app-title-main">{title}</div>
              <div class="app-title-sub">{subtitle}</div>
            </div>
          </div>
          <div class="app-header-right">
            <div>Strategy Desk · Demo</div>
            <div>Built for options workflow</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
