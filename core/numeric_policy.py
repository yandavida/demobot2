"""SSOT-aligned numeric policy constants.

This module defines policy-level labels and structures for numeric
representation, units, and tolerances.

No rounding in core computations.

No behavior changes; usage is opt-in by tests and future gates.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

# Units policy (labels only)
# Base conventions
RATE_UNIT = "decimal"       # 0.05 == 5%
VOL_UNIT = "decimal"        # 0.20 == 20%
TIME_UNIT = "years"
PRICE_UNIT = "currency"

# Greeks canonical units (LOCKED)
VEGA_UNIT = "per_1pct_iv"          # per 0.01 vol decimal
THETA_UNIT = "per_calendar_day"    # per day, ÷365
DELTA_UNIT = "per_1_underlying"
GAMMA_UNIT = "per_1_underlying_sq"
RHO_UNIT = "per_1_rate_decimal"


@dataclass(frozen=True)
class Tolerance:
    abs: Optional[float]
    rel: Optional[float]


class MetricClass(Enum):
    PRICE = "price"
    RATE = "rate"
    VOL = "vol"
    DELTA = "delta"
    GAMMA = "gamma"
    VEGA = "vega"
    THETA = "theta"
    RHO = "rho"
    PNL = "pnl"


# DEFAULT_TOLERANCES is intentionally placeholder-only; concrete values
# will be pinned in a future Gate (N3) based on golden micro cases.
DEFAULT_TOLERANCES: Dict[MetricClass, Tolerance] = {
    mc: Tolerance(abs=None, rel=None) for mc in MetricClass
}


__all__ = [
    "RATE_UNIT",
    "VOL_UNIT",
    "TIME_UNIT",
    "PRICE_UNIT",
    "VEGA_UNIT",
    "THETA_UNIT",
    "DELTA_UNIT",
    "GAMMA_UNIT",
    "RHO_UNIT",
    "Tolerance",
    "MetricClass",
    "DEFAULT_TOLERANCES",
]
