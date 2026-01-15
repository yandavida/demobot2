from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


HedgeType = Literal["delta"]


class HedgeInput(BaseModel):
    delta_portfolio: float
    delta_hedge: float


class HedgeResidualsOut(BaseModel):
    delta: float


class HedgeResultOut(BaseModel):
    hedge_type: HedgeType
    hedge_quantity: float
    residuals: HedgeResidualsOut


__all__ = ["HedgeType", "HedgeInput", "HedgeResidualsOut", "HedgeResultOut"]
