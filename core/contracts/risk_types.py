from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Tuple

from core.portfolio.models import Currency


@dataclass(frozen=True)
class PriceResult:
    """Pricing output for a single unit/contract.

    PV is per-unit (not scaled by quantity). Currency is the instrument's
    native currency. Breakdown holds per-key components (e.g., greeks).
    """

    pv: float
    currency: Currency
    breakdown: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Greeks:
    """Per-unit Greeks exposure.

    Fields represent mathematical derivatives per unit/contract:
      - delta: dPV / dSpot
      - gamma: d2PV / dSpot2
      - vega: dPV / dVol (absolute vol)
      - theta: dPV / dT (time)
      - rho: dPV / dr (interest rate)

    Values are per-unit and should be scaled only by portfolio aggregation
    logic (no scaling inside pricing engines).
    """

    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float


@dataclass(frozen=True)
class RiskScenarioResult:
    scenario_name: str
    base_total_pv: float
    scenario_total_pv: float
    delta_pv_abs: float
    delta_pv_pct: float
    per_symbol_delta_pv: Tuple[Tuple[str, float], ...]
    per_symbol_delta_greeks: Tuple[Tuple[str, Greeks], ...]


@dataclass(frozen=True)
class PortfolioRiskSnapshot:
    """Aggregated portfolio risk snapshot.

    Represents scaled values: total PV and aggregated Greeks are post-scaling
    and reported in `currency` (the portfolio base currency).
    """

    total_pv: float
    currency: Currency
    greeks: Greeks
    positions: Tuple[Tuple[str, float], ...] = tuple()


__all__ = ["PriceResult", "Greeks", "RiskScenarioResult", "PortfolioRiskSnapshot"]
