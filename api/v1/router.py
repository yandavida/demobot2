# api/v1/router.py
from __future__ import annotations

from fastapi import APIRouter, Depends

from saas.context import RequestContext
from core.models import Leg, Position
from core.saas_service import SaasAnalysisService

from .dependencies import get_request_context
from .schemas import (
    HealthResponse,
    CustomerOut,
    CustomerConfigOut,
    MeResponse,
    LimitsResponse,
    LegIn,
    PositionPriceRequest,
    PositionPriceResponse,
    BuilderAnalysisRequest,
    BuilderAnalysisResponse,
)

router = APIRouter(
    prefix="/v1",
    tags=["v1"],
)


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _compute_net_credit_per_unit(position: Position) -> float:
    """
    קרדיט/דביט נטו לפוזיציה (פר יחידה), ללא מכפיל חוזה.
    לוגיקה פשוטה – זהה למה שהיה ב-UI.
    """
    net = 0.0
    for leg in position.legs:
        sign = 1 if leg.side == "short" else -1
        net += sign * leg.premium * leg.quantity
    return net


def _legs_in_to_position(legs_in: list[LegIn]) -> Position:
    """המרה מ־LegIn (Pydantic) ל־Position של הדומיין."""
    legs: list[Leg] = []
    for leg_in in legs_in:
        legs.append(
            Leg(
                side=leg_in.side,
                cp=leg_in.cp,
                strike=leg_in.strike,
                quantity=leg_in.quantity,
                premium=leg_in.premium,
            )
        )
    return Position(legs=legs)


# -------------------------------------------------
# Health / Me / Limits
# -------------------------------------------------
@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """בדיקת חיים בסיסית ל-API v1."""
    return HealthResponse(status="ok", version="1.0.0")


@router.get("/me", response_model=MeResponse)
async def get_me(
    ctx: RequestContext = Depends(get_request_context),
) -> MeResponse:
    """
    מחזיר מידע על הלקוח הנוכחי + הקונפיגורציה שלו.
    """
    customer_out = CustomerOut(**ctx.customer.__dict__)
    config_out = CustomerConfigOut(**ctx.config.__dict__)
    return MeResponse(customer=customer_out, config=config_out)


@router.get("/limits", response_model=LimitsResponse)
async def get_limits(
    ctx: RequestContext = Depends(get_request_context),
) -> LimitsResponse:
    """
    מחזיר מגבלות עיקריות לפי הקונפיגורציה של הלקוח.
    """
    return LimitsResponse(
        max_open_positions=ctx.config.max_open_positions,
        max_notional_exposure=ctx.config.max_notional_exposure,
        feature_flags=ctx.config.feature_flags,
    )


# -------------------------------------------------
# /position/price – קרדיט נטו בלבד
# -------------------------------------------------
@router.post("/position/price", response_model=PositionPriceResponse)
async def price_position(
    payload: PositionPriceRequest,
    ctx: RequestContext = Depends(get_request_context),
) -> PositionPriceResponse:
    """
    Endpoint ראשון:
    מקבל פוזיציה (legs) ומחזיר קרדיט נטו לפוזיציה.
    בעתיד אפשר להרחיב ל-Greeks, Payoff וכו'.
    """

    # המרה ל-Position דומייני
    position = _legs_in_to_position(payload.legs)

    net_credit_per_unit = _compute_net_credit_per_unit(position)
    total_credit = net_credit_per_unit  # לעת עתה אין מכפיל חוזה ברמת ה-API

    # כאן אפשר בעתיד להשתמש ב-ctx.config כדי להפיק אזהרות סיכון חכמות
    risk_warnings: list[str] = []

    return PositionPriceResponse(
        net_credit_per_unit=net_credit_per_unit,
        total_credit=total_credit,
        risk_warnings=risk_warnings,
    )


# -------------------------------------------------
# /position/analyze – ניתוח מלא (Builder)
# -------------------------------------------------
@router.post("/position/analyze", response_model=BuilderAnalysisResponse)
async def analyze_position(
    payload: BuilderAnalysisRequest,
    ctx: RequestContext = Depends(get_request_context),
) -> BuilderAnalysisResponse:
    """
    Endpoint SaaS מרכזי:
    מקבל פוזיציה (legs) + פרמטרים שוקיים (BuilderMarketParams),
    מריץ את SaasAnalysisService ומחזיר ניתוח מלא:
    - P/L
    - Greeks
    - Risk
    - אסטרטגיה מזוהה
    """

    # המרה מ-LegIn (Pydantic) ל-Leg דומייני
    legs: list[Leg] = [
        Leg(
            side=leg_in.side,
            cp=leg_in.cp,
            strike=leg_in.strike,
            quantity=leg_in.quantity,
            premium=leg_in.premium,
        )
        for leg_in in payload.legs
    ]

    service = SaasAnalysisService(ctx)

    result = service.analyze_builder_position(
        legs=legs,
        spot=payload.market.spot,
        lower_factor=payload.market.lower_factor,
        upper_factor=payload.market.upper_factor,
        num_points=payload.market.num_points,
        dte_days=payload.market.dte_days,
        iv=payload.market.iv,
        r=payload.market.r,
        q=payload.market.q,
        contract_multiplier=payload.market.contract_multiplier,
        invested_override=payload.market.invested_capital_override,
    )

    # המרת DataFrame → רשימות למענה JSON
    curve = (
        result.curve_df.to_dict(orient="records")
        if result.curve_df is not None and not result.curve_df.empty
        else []
    )
    scenarios = (
        result.scenarios_df.to_dict(orient="records")
        if result.scenarios_df is not None and not result.scenarios_df.empty
        else []
    )

    strategy = result.strategy_info
    strategy_subtype = getattr(strategy, "subtype", None)
    strategy_description = getattr(strategy, "description", None)

    return BuilderAnalysisResponse(
        net_credit_per_unit=result.net_credit_per_unit,
        total_credit=result.total_credit,
        break_even_points=result.break_even_points,
        pl_summary=result.pl_summary,
        greeks=result.greeks,
        risk_profile=result.risk_profile,
        curve=curve,
        scenarios=scenarios,
        strategy_name=strategy.name,
        strategy_subtype=strategy_subtype,
        strategy_description=strategy_description,
    )
