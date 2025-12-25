from pydantic import BaseModel
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
