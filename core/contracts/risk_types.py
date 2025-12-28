
from __future__ import annotations
from core.portfolio.models import Currency
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.risk.portfolio import PositionRisk

from dataclasses import dataclass
from typing import Tuple






@dataclass(frozen=True)
class Greeks:
    """Per-unit Greeks exposure (canonical units).

    Fields:
        - delta: dPV / dSpot
        - gamma: d2PV / dSpot2
        - vega: change for +1% IV (per 0.01 vol)
        - theta: change per day
        - rho: dPV / dr (interest rate)

    All values are per-unit and must be scaled by quantity * contract_multiplier for portfolio aggregation.
    Vega/theta units are locked: vega per 1% IV, theta per day.
    American options are unsupported in V2-F.1 (must raise if called).
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
    positions: Tuple["PositionRisk", ...] = tuple()


__all__ = ["Greeks", "RiskScenarioResult", "PortfolioRiskSnapshot"]
