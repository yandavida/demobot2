from __future__ import annotations

from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ------------ קלט Planner ------------


class PlannerGoals(BaseModel):
    """העדפות המשתמש ברמת high-level."""

    account_size: Optional[float] = Field(
        default=None,
        description="גודל חשבון משוער (במטבע החשבון)",
    )
    risk_tolerance: Literal["low", "medium", "high"] = Field(
        ...,
        description="רמת סיכון רצויה",
    )
    view: Literal["bullish", "bearish", "neutral", "range"] = Field(
        ...,
        description="כיוון שוק משוער",
    )
    time_horizon_days: int = Field(
        ...,
        ge=1,
        le=365,
        description="טווח זמן רצוי באסטרטגיה (ימים)",
    )
    target_profit_pct: Optional[float] = Field(
        default=None,
        description="יעד תשואה ביחס לחשבון (אם יש, באחוזים)",
    )
    max_loss_pct: Optional[float] = Field(
        default=None,
        description="הפסד מקסימלי נסבל ביחס לחשבון (אם יש, באחוזים)",
    )
    allow_short_options: bool = Field(
        default=True,
        description="האם מותר לכתוב אופציות (short)",
    )
    allow_multi_leg: bool = Field(
        default=True,
        description="האם מותר אסטרטגיות מרובות רגליים",
    )


class MarketSnapshot(BaseModel):
    """תנאי שוק בסיסיים לאסטרטגיה."""

    symbol: str = Field(..., description="סימול נכס הבסיס")
    spot: float = Field(..., gt=0, description="מחיר נכס בסיס")
    expiry: date = Field(..., description="תאריך פקיעת האופציות")
    iv: Optional[float] = Field(
        default=None,
        description="סטיית תקן מרומזת (אופציונלי)",
    )
    r: Optional[float] = Field(
        default=None,
        description="ריבית חסרת סיכון (אופציונלי)",
    )
    q: Optional[float] = Field(
        default=None,
        description="דיבידנד/תשואת נכס (אופציונלי)",
    )


class StrategySuggestRequest(BaseModel):
    """קלט מלא ל-Planner – Goals + תנאי שוק."""

    goals: PlannerGoals
    market: MarketSnapshot


# ------------ פלט Planner ------------


class StrategyLeg(BaseModel):
    side: Literal["long", "short"]
    cp: Literal["CALL", "PUT"]
    strike: float
    quantity: int = 1
    expiry: date
    premium: Optional[float] = None


class PayoffSummary(BaseModel):
    max_profit: Optional[float] = None
    max_loss: Optional[float] = None
    breakeven_low: Optional[float] = None
    breakeven_high: Optional[float] = None


class StrategySuggestion(BaseModel):
    name: str
    subtype: str
    legs: List[StrategyLeg]
    payoff_summary: PayoffSummary
    risk_score: float = Field(..., ge=0, le=1)
    explanation_tokens: List[str] = Field(
        default_factory=list,
        description="Bullets/tokens להסבר אסטרטגיה למשתמש",
    )


class StrategySuggestResponse(BaseModel):
    strategies: List[StrategySuggestion]
