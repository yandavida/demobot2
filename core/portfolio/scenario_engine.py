from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from core.portfolio.portfolio_models import PortfolioState
from core.pricing.context import PricingContext
from core.pricing.engine import PricingEngine
from core.scenarios.types import ScenarioSet
from core.scenarios.apply import build_shocked_context
# import risk utilities lazily inside functions to avoid broad mypy import chains


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    total_pv: float
    greeks: object
    currency: str


@dataclass(frozen=True)
class ScenarioReport:
    results: Tuple[ScenarioResult, ...]

    def __post_init__(self) -> None:
        sorted_results = tuple(sorted(self.results, key=lambda r: r.name))
        object.__setattr__(self, "results", sorted_results)


def run_portfolio_scenarios(
    state: PortfolioState,
    base_context: PricingContext,
    pricing_engine: PricingEngine,
    scenario_set: ScenarioSet,
) -> ScenarioReport:
    results: list[ScenarioResult] = []

    for sc in scenario_set.scenarios:
        ctx = build_shocked_context(base_context, sc)
        # evaluate positions with shocked market and vol provider
        from core.risk.portfolio import valuate_and_risk_positions, aggregate_portfolio_risk

        positions = valuate_and_risk_positions(state=state, pricing_engine=pricing_engine, snapshot=ctx.market, base_currency=state.base_currency, context=ctx)
        agg = aggregate_portfolio_risk(positions, base_currency=state.base_currency)

        results.append(ScenarioResult(name=sc.name, total_pv=float(agg.total_pv), greeks=agg.greeks, currency=agg.currency))

    return ScenarioReport(results=tuple(results))


__all__ = ["ScenarioResult", "ScenarioReport", "run_portfolio_scenarios"]
