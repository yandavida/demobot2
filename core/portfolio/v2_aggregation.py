from __future__ import annotations
from typing import Tuple, Dict
from core.portfolio.v2_models import PortfolioStateV2, Greeks

from dataclasses import dataclass

Money = float  # For now

@dataclass(frozen=True)
class ExposureV2:
    abs_notional: float
    delta: float

# Forward declaration for type checking
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.portfolio.v2_constraints import ConstraintsReportV2

@dataclass(frozen=True)
class PortfolioTotalsV2:
    pv: Money
    greeks: Greeks
    exposures: Tuple[Tuple[str, ExposureV2], ...]  # (underlying, ExposureV2)
    constraints: 'ConstraintsReportV2'

def aggregate_portfolio(state: PortfolioStateV2) -> PortfolioTotalsV2:
    pv = 0.0
    greeks = Greeks(delta=0.0, gamma=0.0, vega=0.0, theta=0.0, rho=0.0)
    exposures: Dict[str, ExposureV2] = {}
    for pos in state.positions.values():
        for leg in pos.legs:
            scale = leg.quantity
            pv += leg.pv_per_unit * scale
            greeks = Greeks(
                delta=greeks.delta + leg.greeks_per_unit.delta * scale,
                gamma=greeks.gamma + leg.greeks_per_unit.gamma * scale,
                vega=greeks.vega + leg.greeks_per_unit.vega * scale,
                theta=greeks.theta + leg.greeks_per_unit.theta * scale,
                rho=greeks.rho + leg.greeks_per_unit.rho * scale,
            )
            ex = exposures.get(leg.underlying)
            abs_notional = abs(scale) * leg.notional_per_unit
            delta = leg.greeks_per_unit.delta * scale
            if ex:
                exposures[leg.underlying] = ExposureV2(
                    abs_notional=ex.abs_notional + abs_notional,
                    delta=ex.delta + delta,
                )
            else:
                exposures[leg.underlying] = ExposureV2(abs_notional=abs_notional, delta=delta)
    exposures_tuple = tuple(sorted(exposures.items(), key=lambda x: x[0]))
    # Constraints will be filled in by constraints engine
    from core.portfolio.v2_constraints import empty_constraints_report
    return PortfolioTotalsV2(
        pv=pv,
        greeks=greeks,
        exposures=exposures_tuple,
        constraints=empty_constraints_report(),
    )
