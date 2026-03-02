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


def _ensure_positive(value: float, name: str) -> None:
    """Ensure value is strictly positive (> 0)."""
    if value <= 0:
        raise ValueError(f"{name} must be positive (> 0), got {value}")


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
        if self.notional <= 0:
            raise ValueError("notional must be positive")
        if self.forward_rate is not None:
            _ensure_finite(self.forward_rate, "forward_rate")
        if self.direction is not None:
            if self.direction not in ("receive_foreign_pay_domestic", "pay_foreign_receive_domestic"):
                raise ValueError(f"Invalid direction: {self.direction}")


@dataclass(frozen=True)
class FxConventions:
    day_count: str
    compounding: str
    domestic_currency: Optional[str] = None

    def __post_init__(self):
        if self.domestic_currency is not None and self.domestic_currency.strip() == "":
            raise ValueError("domestic_currency must be non-empty when provided")


@dataclass(frozen=True)
class FxMarketSnapshot:
    as_of_ts: datetime.datetime
    spot_rate: float
    conventions: Optional[FxConventions] = None
    df_domestic: Optional[float] = None
    df_foreign: Optional[float] = None
    domestic_currency: Optional[str] = None

    def __post_init__(self):
        if self.as_of_ts is None:
            raise ValueError("as_of_ts is required for market snapshots")
        _ensure_finite(self.spot_rate, "spot_rate")
        if self.df_domestic is not None:
            _ensure_finite(self.df_domestic, "df_domestic")
            _ensure_positive(self.df_domestic, "df_domestic")
        if self.df_foreign is not None:
            _ensure_finite(self.df_foreign, "df_foreign")
            _ensure_positive(self.df_foreign, "df_foreign")
        if self.domestic_currency is not None and self.domestic_currency.strip() == "":
            raise ValueError("domestic_currency must be non-empty when provided")


@dataclass(frozen=True)
class PricingResult:
    as_of_ts: datetime.datetime
    pv: float
    details: Optional[dict] = None
    currency: Optional[str] = None
    metric_class: Optional[numeric_policy.MetricClass] = None

    def __post_init__(self):
        if self.as_of_ts is None:
            raise ValueError("as_of_ts is required for PricingResult")
        _ensure_finite(self.pv, "pv")
        if self.currency is not None and self.currency.strip() == "":
            raise ValueError("currency must be non-empty when provided")


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
