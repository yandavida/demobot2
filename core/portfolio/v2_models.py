from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, Optional

# --- Domain types ---

Currency = str  # ISO code, e.g. "USD"

@dataclass(frozen=True)
class PortfolioConstraintsV2:
    max_notional: Optional[float] = None
    max_abs_delta: Optional[float] = None
    max_concentration_pct: Optional[float] = None

@dataclass(frozen=True)
class Greeks:
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float

@dataclass(frozen=True)
class LegV2:
    leg_id: str
    underlying: str
    pv_per_unit: float
    greeks_per_unit: Greeks
    notional_per_unit: float
    quantity: float

@dataclass(frozen=True)
class PositionV2:
    position_id: str
    legs: Tuple[LegV2, ...]

@dataclass(frozen=True)
class PortfolioStateV2:
    base_currency: Currency
    constraints: PortfolioConstraintsV2
    positions: Dict[str, PositionV2]
