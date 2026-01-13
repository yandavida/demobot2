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
    TIME = "time"
    RHO = "rho"
    PNL = "pnl"


# DEFAULT_TOLERANCES is populated with conservative, wide-first
# initial tolerance values. These are policy values only and may be
# tightened in a future Gate (N3) once empirical baselines exist.
DEFAULT_TOLERANCES: Dict[MetricClass, Tolerance] = {
    MetricClass.PRICE: Tolerance(abs=1e-6, rel=1e-8),
    MetricClass.RATE: Tolerance(abs=1e-10, rel=1e-8),
    MetricClass.VOL: Tolerance(abs=1e-10, rel=1e-8),

    MetricClass.DELTA: Tolerance(abs=1e-8, rel=1e-8),
    MetricClass.GAMMA: Tolerance(abs=1e-10, rel=1e-8),
    MetricClass.VEGA: Tolerance(abs=1e-6, rel=1e-6),
    MetricClass.THETA: Tolerance(abs=1e-6, rel=1e-6),
    MetricClass.TIME: Tolerance(abs=1e-6, rel=1e-6),
    MetricClass.RHO: Tolerance(abs=1e-6, rel=1e-6),

    MetricClass.PNL: Tolerance(abs=1e-6, rel=1e-6),
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
