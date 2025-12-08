# api/v1/schemas.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
from typing import Literal

from pydantic import BaseModel
from saas.models import PlanTier


# -------------------------------------------------
# Leg / Pricing basic
# -------------------------------------------------
class LegIn(BaseModel):
    """Leg יחיד שנכנס מה-API."""

    side: Literal["long", "short"]
    cp: Literal["CALL", "PUT"]
    strike: float
    quantity: int = 1
    premium: float = 0.0


class PositionPriceRequest(BaseModel):
    """בקשה לתמחור פוזיציה בסיסית – רק קרדיט נטו."""

    legs: List[LegIn]


class PositionPriceResponse(BaseModel):
    net_credit_per_unit: float
    total_credit: float
    # אזהרות סיכון לוגיות (לפי הקונפיגורציה של הלקוח)
    risk_warnings: List[str] = []


# -------------------------------------------------
# SaaS – Health / Me / Limits
# -------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    version: str


class CustomerOut(BaseModel):
    id: str
    name: str
    plan: PlanTier
    is_active: bool


class CustomerConfigOut(BaseModel):
    customer_id: str
    display_name: str

    default_underlying: Optional[str] = None
    max_open_positions: int
    max_notional_exposure: Optional[float] = None

    feature_flags: Dict[str, bool]
    risk_profile: str


class MeResponse(BaseModel):
    customer: CustomerOut
    config: CustomerConfigOut


class LimitsResponse(BaseModel):
    max_open_positions: int
    max_notional_exposure: Optional[float] = None
    feature_flags: Dict[str, bool]


# -------------------------------------------------
# Builder – ניתוח פוזיציה מלאה
# -------------------------------------------------
class BuilderMarketParams(BaseModel):
    """
    פרמטרים שוקיים לניתוח פוזיציית Builder.
    """

    spot: float
    lower_factor: float = 0.8
    upper_factor: float = 1.2
    num_points: int = 201
    dte_days: int = 30
    iv: float = 0.20  # 20% IV
    r: float = 0.02  # 2% risk-free
    q: float = 0.0  # 0% dividend / carry
    contract_multiplier: int = 100
    invested_capital_override: float | None = None


class BuilderAnalysisRequest(BaseModel):
    """
    בקשה מלאה לניתוח פוזיציה:
    - רשימת רגליים
    - פרמטרים שוקיים
    """

    legs: List[LegIn]
    market: BuilderMarketParams


class BuilderAnalysisResponse(BaseModel):
    """
    תגובה לניתוח פוזיציה:
    - קרדיט/דביט
    - סיכום PL
    - Greeks
    - פרופיל סיכון
    - עקומת P/L
    - טבלת תרחישים
    - פרטי אסטרטגיה מזוהה
    """

    net_credit_per_unit: float
    total_credit: float

    break_even_points: List[float]
    pl_summary: Dict[str, Any]
    greeks: Dict[str, Any]
    risk_profile: Dict[str, Any]

    curve: List[Dict[str, Any]]
    scenarios: List[Dict[str, Any]]

    strategy_name: str
    strategy_subtype: Optional[str] = None
    strategy_description: Optional[str] = None
