"""FX pricing boundary types for Institutional MTM (Gate F8.1).

This module defines contract, snapshot, conventions, and result types
as immutable dataclasses with deterministic validation. No pricing
formulas or MTM logic are implemented here (F8.2).
"""
from __future__ import annotations

from dataclasses import dataclass
import datetime
import math
from typing import Optional

from core import numeric_policy


def _ensure_finite(value: float, name: str) -> None:
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")


@dataclass(frozen=True)
class FXForwardContract:
    base_currency: str
    quote_currency: str
    notional: float
    forward_date: datetime.date
    forward_rate: Optional[float] = None
    direction: Optional[str] = None

    def __post_init__(self):
        _ensure_finite(self.notional, "notional")
        if self.forward_rate is not None:
            _ensure_finite(self.forward_rate, "forward_rate")
        if self.direction is not None:
            if self.direction not in ("receive_foreign_pay_domestic", "pay_foreign_receive_domestic"):
                raise ValueError(f"Invalid direction: {self.direction}")


@dataclass(frozen=True)
class FxConventions:
    day_count: str
    compounding: str


@dataclass(frozen=True)
class FxMarketSnapshot:
    as_of_ts: datetime.datetime
    spot_rate: float
    conventions: Optional[FxConventions] = None
    df_domestic: Optional[float] = None
    df_foreign: Optional[float] = None

    def __post_init__(self):
        if self.as_of_ts is None:
            raise ValueError("as_of_ts is required for market snapshots")
        _ensure_finite(self.spot_rate, "spot_rate")
        if self.df_domestic is not None:
            _ensure_finite(self.df_domestic, "df_domestic")
        if self.df_foreign is not None:
            _ensure_finite(self.df_foreign, "df_foreign")


@dataclass(frozen=True)
class PricingResult:
    as_of_ts: datetime.datetime
    pv: float
    details: Optional[dict] = None

    def __post_init__(self):
        if self.as_of_ts is None:
            raise ValueError("as_of_ts is required for PricingResult")
        _ensure_finite(self.pv, "pv")


# Exported names
__all__ = [
    "FXForwardContract",
    "FxMarketSnapshot",
    "FxConventions",
    "PricingResult",
]

# Expose the numeric policy used for any future comparisons
# (keeps the module explicit about numeric tolerances and avoids
# accidental local epsilons elsewhere).
_DEFAULT_TOLERANCES = numeric_policy.DEFAULT_TOLERANCES
