from typing import Literal, Optional, Dict
from pydantic import BaseModel, model_validator

from api.v2.portfolio_schemas import MoneyOut


class AmericanOptionGreeksOut(BaseModel):
    delta: Optional[float] = None
    gamma: Optional[float] = None
    vega: Optional[float] = None
    theta: Optional[float] = None
    # static units metadata (non-dynamic, must be stable strings)
    units: Dict[str, str] = {"theta": "per_day", "vega": "per_1pct"}


class AmericanOptionValuationOut(BaseModel):
    # Contractual identifiers
    symbol: str
    option_type: Literal["call", "put"]
    style: Literal["american"] = "american"

    # Market inputs / params (use primitive types to avoid datetime/dynamic fields)
    spot: float
    strike: float
    expiry: str  # ISO date string (avoid datetime types at the contract boundary)
    rate: Optional[float] = None
    div_yield: Optional[float] = None
    vol: Optional[float] = None

    # Result fields
    price: MoneyOut
    greeks: Optional[AmericanOptionGreeksOut] = None

    @model_validator(mode="after")
    def _canonicalize(self) -> "AmericanOptionValuationOut":
        # Future-proof hook to canonicalize list-like children (none today)
        return self
