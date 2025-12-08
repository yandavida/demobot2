# ui/strategy_services.py
from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Dict, List, Tuple

import pandas as pd
import plotly.express as px

from core.models import Leg, Position
from core.strategy_brain import StrategyBrain, AnalysisConfig, Domain, AnalysisLayer
from core.backtest_engine import BacktestConfig
from core.strategy_detector import detect_strategy

from ui.api_client import analyze_position_v1


# ============================================================
#  Data classes
# ============================================================


@dataclass
class BuilderAnalysisResult:
    curve_df: pd.DataFrame
    be_points: List[float]
    scenarios_df: pd.DataFrame
    pl_summary: Dict[str, Any]
    greeks: Dict[str, Any]
    risk_profile: Dict[str, Any]
    strategy_info: Any  # אובייקט עם .name / .subtype / .description
    net_credit: float
    total_credit: float
    risk_warnings: List[str]


# ============================================================
#  Helpers – DF <-> Position + ברירות מחדל + גרפים
# ============================================================


def df_to_position(df: pd.DataFrame) -> Position:
    """המרת DataFrame של רגליים לפוזיציית דומיין."""
    legs: List[Leg] = []

    for _, row in df.iterrows():
        try:
            side = str(row.get("side", "")).lower()
            cp_raw = str(row.get("cp", "")).upper()
            strike = float(row.get("strike"))
        except Exception:
            continue

        if side not in ("long", "short"):
            continue
        if cp_raw not in ("CALL", "PUT"):
            continue

        try:
            quantity = int(row.get("quantity", 1))
        except Exception:
            quantity = 1

        try:
            premium = float(row.get("premium", 0.0))
        except Exception:
            premium = 0.0

        legs.append(
            Leg(
                side=side,  # type: ignore[arg-type]
                cp=cp_raw,  # type: ignore[arg-type]
                strike=strike,
                quantity=quantity,
                premium=premium,
            )
        )

    return Position(legs=legs)


def get_default_legs_df() -> pd.DataFrame:
    """
    פוזיציית דוגמה לברירת מחדל ב־Builder.
    (לא קריטי מתמטית – רק UX).
    """
    data = [
        {"side": "short", "cp": "PUT", "strike": 4900.0, "quantity": 1, "premium": 4.0},
        {"side": "long", "cp": "PUT", "strike": 4800.0, "quantity": 1, "premium": 2.0},
        {
            "side": "short",
            "cp": "CALL",
            "strike": 5100.0,
            "quantity": 1,
            "premium": 4.2,
        },
        {"side": "long", "cp": "CALL", "strike": 5200.0, "quantity": 1, "premium": 2.1},
    ]
    return pd.DataFrame(data)


def make_builder_figures(
    *,
    curve_df: pd.DataFrame,
    be_points: List[float],
    spot: float,
    max_profit: float,
) -> Tuple[Any, Any]:
    """
    בונה שני גרפים:
    - fig_full: טווח מלא
    - fig_zoom: זום סביב האפס
    """
    if curve_df is None or curve_df.empty:
        return None, None

    # --- גרף מלא ---
    fig_full = px.line(curve_df, x="price", y="pl")
    fig_full.update_layout(
        height=420,
        margin=dict(l=60, r=40, t=40, b=60),
        xaxis_title="מחיר נכס",
        yaxis_title="P/L (בסכום מלא)",
    )
    fig_full.add_hline(y=0, line_dash="dash")
    fig_full.add_vline(x=spot, line_dash="dot")
    for be in be_points:
        fig_full.add_vline(x=be, line_dash="dot", opacity=0.4)

    # --- זום סביב האפס ---
    if max_profit != 0:
        zoom_df = curve_df.copy()
        y_lim = 2 * abs(max_profit)

        fig_zoom = px.line(zoom_df, x="price", y="pl")
        fig_zoom.update_layout(
            height=420,
            margin=dict(l=60, r=40, t=40, b=60),
            xaxis_title="מחיר נכס",
            yaxis_title="P/L (זום סביב 0)",
        )
        fig_zoom.add_hline(y=0, line_dash="dash")
        fig_zoom.add_vline(x=spot, line_dash="dot")
        for be in be_points:
            fig_zoom.add_vline(x=be, line_dash="dot", opacity=0.4)

        fig_zoom.update_yaxes(range=[-y_lim, y_lim])
    else:
        fig_zoom = None

    return fig_full, fig_zoom


# ============================================================
#  Analysis – SaaS first, local fallback
# ============================================================


def run_builder_analysis(
    *,
    legs_df: pd.DataFrame,
    spot: float,
    lower_factor: float,
    upper_factor: float,
    num_points: int,
    dte_days: int,
    iv: float,
    r: float,
    q: float,
    contract_multiplier: int,
    invested_override: float | None,
) -> BuilderAnalysisResult:
    """
    פונקציית הניתוח המרכזית של ה־Builder:
    1. קודם מנסה לקרוא ל־/v1/position/analyze (SaaS backend)
    2. אם יש תקלה (חיבור / שרת / JSON) – נופלת לניתוח לוקאלי עם StrategyBrain
    """

    # ---- שלב 1: ניסיון SaaS ----
    try:
        data = analyze_position_v1(
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

        curve_df = pd.DataFrame(data.get("curve", []))
        scenarios_df = pd.DataFrame(data.get("scenarios", []))

        be_points = list(data.get("break_even_points", []))
        pl_summary = dict(data.get("pl_summary", {}))
        greeks = dict(data.get("greeks", {}))
        risk_profile = dict(data.get("risk_profile", {}))

        net_credit = float(data.get("net_credit_per_unit", 0.0))
        total_credit = float(data.get("total_credit", 0.0))

        # אזהרות סיכון – אפשר לשלוף מתוך risk_profile אם יש שם
        risk_warnings = list(risk_profile.get("warnings", []))

        strategy_info = SimpleNamespace(
            name=data.get("strategy_name", "Unknown strategy"),
            subtype=data.get("strategy_subtype"),
            description=data.get("strategy_description"),
        )

        return BuilderAnalysisResult(
            curve_df=curve_df,
            be_points=be_points,
            scenarios_df=scenarios_df,
            pl_summary=pl_summary,
            greeks=greeks,
            risk_profile=risk_profile,
            strategy_info=strategy_info,
            net_credit=net_credit,
            total_credit=total_credit,
            risk_warnings=risk_warnings,
        )

    except Exception:
        # לא זורקים החוצה – ניתן ל־UI חוויה "שקטה" ונשתמש בלוקאלי.
        pass

    # ---- שלב 2: Fallback לוקאלי ----
    return _run_builder_analysis_local(
        legs_df=legs_df,
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


def _run_builder_analysis_local(
    *,
    legs_df: pd.DataFrame,
    spot: float,
    lower_factor: float,
    upper_factor: float,
    num_points: int,
    dte_days: int,
    iv: float,
    r: float,
    q: float,
    contract_multiplier: int,
    invested_override: float | None,
) -> BuilderAnalysisResult:
    """
    ניתוח לוקאלי – משתמש ב-StrategyBrain ו-BacktestEngine.
    זה נכנס לפעולה רק אם ה-API לא זמין.
    """

    position = df_to_position(legs_df)
    if position.is_empty():
        raise ValueError("Empty position – no valid legs found")

    bt_cfg = BacktestConfig(
        position=position,
        spot=spot,
        lower_factor=lower_factor,
        upper_factor=upper_factor,
        num_points=num_points,
        dte_days=dte_days,
        iv=iv,
        r=r,
        q=q,
        contract_multiplier=contract_multiplier,
    )

    config = AnalysisConfig(
        domain=Domain.OPTIONS,
        enabled_layers=[AnalysisLayer.BACKTEST],
        goals=None,
        backtest_config=bt_cfg,
        flags={"invested_capital_override": invested_override},
    )

    brain = StrategyBrain()
    analysis = brain.analyze_position(position, config)

    curve_df = analysis.curve_df if analysis.curve_df is not None else pd.DataFrame()
    scenarios_df = (
        analysis.scenarios_df if analysis.scenarios_df is not None else pd.DataFrame()
    )
    be_points = analysis.break_even_points or []
    pl_summary = analysis.pl_summary or {}
    greeks = analysis.greeks or {}
    risk_profile = analysis.risk_profile or {}

    # זיהוי אסטרטגיה בסיסי
    strategy_info_core = detect_strategy(
        position=position,
        spot=spot,
        curve_df=curve_df,
        be_points=be_points,
    )
    strategy_info = SimpleNamespace(
        name=strategy_info_core.name,
        subtype=getattr(strategy_info_core, "subtype", None),
        description=getattr(strategy_info_core, "description", None),
    )

    # קרדיט נטו – חישוב פשוט לוקאלי
    net_credit = 0.0
    for _, row in legs_df.iterrows():
        try:
            side = str(row.get("side", "")).lower()
            premium = float(row.get("premium", 0.0))
            qty = int(row.get("quantity", 1))
        except Exception:
            continue

        sign = 1.0 if side == "short" else -1.0
        net_credit += sign * premium * qty

    total_credit = net_credit * contract_multiplier
    risk_warnings: List[str] = list(risk_profile.get("warnings", []))

    return BuilderAnalysisResult(
        curve_df=curve_df,
        be_points=be_points,
        scenarios_df=scenarios_df,
        pl_summary=pl_summary,
        greeks=greeks,
        risk_profile=risk_profile,
        strategy_info=strategy_info,
        net_credit=net_credit,
        total_credit=total_credit,
        risk_warnings=risk_warnings,
    )
