from __future__ import annotations

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


class FxRates(BaseModel):
    base_ccy: str
    quotes: Dict[str, float]


class SpotPrices(BaseModel):
    prices: Dict[str, float]
    currency: Dict[str, str]


class Curve(BaseModel):
    day_count: str
    compounding: Literal["continuous", "annual"]
    zero_rates: Dict[str, float]


class InterestRateCurves(BaseModel):
    curves: Dict[str, Curve]


class VolSurface(BaseModel):
    type: str
    data: Any


class VolSurfaces(BaseModel):
    surfaces: Dict[str, VolSurface]


class MarketConventions(BaseModel):
    calendar: str
    day_count_default: str
    spot_lag: int


class MarketSnapshotPayloadV0(BaseModel):
    fx_rates: FxRates
    spots: SpotPrices
    curves: InterestRateCurves
    vols: Optional[VolSurfaces] = None
    conventions: MarketConventions

    model_config = {
        "json_schema_extra": {"examples": []}
    }
