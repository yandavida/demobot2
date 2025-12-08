from __future__ import annotations

from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class FxForwardRequest(BaseModel):
    """קלט לניתוח עסקת FX Forward אחת."""

    base_ccy: str = Field(..., description="מטבע בסיס (למשל 'USD')")
    quote_ccy: str = Field(..., description="מטבע ציטוט (למשל 'ILS')")
    notional: float = Field(..., gt=0, description="נוטיונל במטבע בסיס")
    direction: Literal["BUY", "SELL"] = Field(
        ..., description="כיוון העסקה: BUY/SELL על מטבע הבסיס"
    )

    spot: float = Field(..., gt=0, description="שער ספוט נוכחי")
    forward_rate: float = Field(..., gt=0, description="שער פורוורד מוסכם בעסקה")

    valuation_date: date = Field(..., description="תאריך הערכת העסקה (valuation)")
    maturity_date: date = Field(..., description="תאריך פקיעה/סגירת הפורוורד")

    curve_min_pct: float = Field(
        default=-0.1,
        description="סטייה מינימלית מספוט עבור עקום רווח/הפסד (לדוגמה -0.1 = מינוס 10%)",
    )
    curve_max_pct: float = Field(
        default=0.1,
        description="סטייה מקסימלית מספוט עבור העקום (0.1 = פלוס 10%)",
    )
    curve_points: int = Field(
        default=101, ge=11, le=501, description="מספר נקודות בעקום P&L"
    )


class FxCurvePoint(BaseModel):
    underlying: float = Field(..., description="שער FX (לדוגמה spot/forward scenario)")
    pl: float = Field(..., description="רווח/הפסד בעסקה בשקלים או במטבע בסיס")


class FxPlSummary(BaseModel):
    max_profit: float
    max_loss: float
    expected_pl: Optional[float] = None
    pl_at_spot: Optional[float] = None
    pl_at_forward: Optional[float] = None


class FxRiskProfile(BaseModel):
    risk_level: str = Field(..., description="טקסט כמו 'Low', 'Medium', 'High'")
    risk_score: float = Field(..., ge=0, le=1, description="ניקוד בין 0–1")
    tags: List[str] = Field(default_factory=list)
    comments: List[str] = Field(default_factory=list)


class FxScenarioResult(BaseModel):
    name: str
    description: Optional[str] = None
    pl: float
    probability: Optional[float] = None


class FxForwardResponse(BaseModel):
    curve: List[FxCurvePoint]
    pl_summary: FxPlSummary
    risk_profile: FxRiskProfile
    scenarios: List[FxScenarioResult]
