from __future__ import annotations

from decimal import Decimal
from decimal import InvalidOperation
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel

from core.vol.types import VolKey


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


class VolLookupError(KeyError):
    """Raised when requested vol cannot be resolved from a snapshot payload."""


def _to_key_decimal(value: float) -> Decimal:
    try:
        dec = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"invalid vol key numeric value: {value!r}") from exc
    if not dec.is_finite():
        raise ValueError(f"non-finite vol key numeric value: {value!r}")
    return dec


def make_vol_lookup_key(vol_key: VolKey) -> str:
    """Deterministic string key for v0 vol quote maps.

    Key format:
      <UNDERLYING>|<EXPIRY_T>|<STRIKE_OR_STAR>|<OPTION_TYPE_OR_STAR>
    """
    underlying = str(vol_key.underlying).strip()
    if not underlying:
        raise ValueError("vol_key.underlying must be non-empty")

    expiry_t = str(_to_key_decimal(vol_key.expiry_t))
    strike = "*" if vol_key.strike is None else str(_to_key_decimal(vol_key.strike))
    option_type = "*" if vol_key.option_type is None else str(vol_key.option_type).strip().lower()
    if option_type not in {"*", "call", "put", "c", "p"}:
        raise ValueError("vol_key.option_type must be one of: call, put, c, p, None")

    return f"{underlying}|{expiry_t}|{strike}|{option_type}"


def _coerce_numeric_vol(value: Any, *, source: str) -> float:
    if not isinstance(value, (int, float)):
        raise VolLookupError(f"vol value must be numeric in {source}")
    vol = float(value)
    if vol < 0.0:
        raise VolLookupError(f"vol value must be >= 0 in {source}")
    return vol


def get_vol(payload: MarketSnapshotPayloadV0, vol_key: VolKey) -> float:
    """Resolve vol deterministically from snapshot payload.

    Resolution order (deterministic, no defaulting):
      1) Exact key lookup in any surface data['quotes'] map
      2) Backward-compatible flat surface by underlying name with data['vol']

    Missing values raise VolLookupError.
    """
    if payload.vols is None:
        raise VolLookupError("vols missing in market snapshot payload")

    lookup_key = make_vol_lookup_key(vol_key)

    for name in sorted(payload.vols.surfaces.keys()):
        surface = payload.vols.surfaces[name]
        data = surface.data if isinstance(surface.data, dict) else {}
        quotes = data.get("quotes")
        if isinstance(quotes, dict) and lookup_key in quotes:
            return _coerce_numeric_vol(quotes[lookup_key], source=f"vols.surfaces['{name}'].data.quotes")

    underlying_name = str(vol_key.underlying)
    surface = payload.vols.surfaces.get(underlying_name)
    if surface is not None and isinstance(surface.data, dict) and "vol" in surface.data:
        return _coerce_numeric_vol(surface.data["vol"], source=f"vols.surfaces['{underlying_name}'].data.vol")

    raise VolLookupError(f"vol not found for key '{lookup_key}'")


__all__ = [
    "Curve",
    "FxRates",
    "InterestRateCurves",
    "MarketConventions",
    "MarketSnapshotPayloadV0",
    "SpotPrices",
    "VolLookupError",
    "VolSurface",
    "VolSurfaces",
    "get_vol",
    "make_vol_lookup_key",
]
