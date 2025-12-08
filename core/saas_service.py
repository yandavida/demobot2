# core/saas_service.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd

from saas.context import RequestContext
from core.models import Position, Leg
from core.backtest_engine import BacktestConfig
from core.strategy_brain import StrategyBrain, AnalysisConfig, Domain, AnalysisLayer
from core.strategy_detector import detect_strategy


def _compute_net_credit(position: Position) -> float:
    """
    קרדיט/דביט נטו לפוזיציה (פר יחידה), ללא מכפיל חוזה.
    אותו רעיון כמו ב-UI וב-API v1.
    """
    net = 0.0
    for leg in position.legs:
        sign = 1 if leg.side == "short" else -1
        net += sign * leg.premium * leg.quantity
    return net


@dataclass
class BuilderAnalysisResult:
    """
    תוצאה "עשירה" לניתוח פוזיציה מטאב ה-Builder,
    לשימוש גם ב-API וגם ב-UI בעתיד.
    """

    position: Position
    curve_df: pd.DataFrame
    scenarios_df: pd.DataFrame
    break_even_points: List[float]
    pl_summary: Dict[str, Any]
    greeks: Dict[str, Any]
    risk_profile: Dict[str, Any]
    strategy_info: Any
    net_credit_per_unit: float
    total_credit: float


class SaasAnalysisService:
    """
    Service מרכזי לשכבת ה-SaaS:
    מקבל RequestContext (לקוח + קונפיגורציה),
    ומספק מתודות ניתוח לפוזיציות.
    """

    def __init__(self, ctx: RequestContext) -> None:
        self.ctx = ctx

    def analyze_builder_position(
        self,
        legs: List[Leg],
        *,
        spot: float,
        lower_factor: float,
        upper_factor: float,
        num_points: int,
        dte_days: int,
        iv: float,
        r: float,
        q: float,
        contract_multiplier: int,
        invested_override: float | None = None,
    ) -> BuilderAnalysisResult:
        """
        ניתוח פוזיציה חופשית (טאב Builder):
        - מריץ StrategyBrain עם שכבת BACKTEST
        - מחזיר עקומת P/L, תרחישים, PL summary, Greeks, Risk, Strategy
        - מחשב קרדיט/דביט נטו לפוזיציה
        """

        position = Position(legs=legs)
        if position.is_empty():
            raise ValueError("Position is empty – no valid legs supplied")

        # --- בניית קונפיגורציית Backtest ל-Brain ---
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
            flags={
                # override להון מושקע – כמו ב-UI
                "invested_capital_override": invested_override,
                # מידע SaaSי לשימוש עתידי (לימיטים, פיצ'רים, pricing וכו')
                "customer_id": self.ctx.customer.id,
                "plan_tier": self.ctx.customer.plan.value,
                "risk_profile": self.ctx.config.risk_profile,
            },
        )

        brain = StrategyBrain()
        analysis = brain.analyze_position(position, config)

        curve_df = analysis.curve_df or pd.DataFrame()
        scenarios_df = analysis.scenarios_df or pd.DataFrame()
        pl_summary = analysis.pl_summary or {}
        greeks = analysis.greeks or {}
        risk_profile = analysis.risk_profile or {}
        be_points = analysis.break_even_points or []

        # זיהוי אסטרטגיה (שם, subtype, תיאור)
        strategy_info = detect_strategy(
            position=position,
            spot=spot,
            curve_df=curve_df,
            be_points=be_points,
        )

        # קרדיט/דביט נטו
        net_credit = _compute_net_credit(position)
        total_credit = net_credit  # בעתיד אפשר להכניס מכפיל חוזה / כמות חוזים

        return BuilderAnalysisResult(
            position=position,
            curve_df=curve_df,
            scenarios_df=scenarios_df,
            break_even_points=be_points,
            pl_summary=pl_summary,
            greeks=greeks,
            risk_profile=risk_profile,
            strategy_info=strategy_info,
            net_credit_per_unit=net_credit,
            total_credit=total_credit,
        )
