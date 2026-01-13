from pydantic import BaseModel, model_validator
from typing import List

class MoneyOut(BaseModel):
    value: float
    currency: str

class ExposureOut(BaseModel):
    underlying: str
    abs_notional: float
    delta: float

class ConstraintsOut(BaseModel):
    passed: bool
    breaches: List[str]

class PortfolioSummaryOut(BaseModel):
    session_id: str
    version: int
    pv: MoneyOut
    delta: float
    exposures: List[ExposureOut]
    constraints: ConstraintsOut

    @model_validator(mode="after")
    def _canonicalize_exposures(self) -> "PortfolioSummaryOut":
        # Ensure deterministic canonical ordering for exposures at model boundary
        try:
            self.exposures.sort(key=lambda e: e.underlying)
        except Exception:
            pass
        return self
