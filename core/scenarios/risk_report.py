from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from core.portfolio.portfolio_models import PortfolioState
from core.pricing.context import PricingContext
from core.pricing.engine import PricingEngine
from core.scenarios.types import ScenarioSet
from core.risk.portfolio import (
    valuate_and_risk_positions,
    aggregate_portfolio_risk,
)
from core.contracts.risk_types import Greeks, PortfolioRiskSnapshot, RiskScenarioResult
from core.scenarios.apply import build_shocked_context


@dataclass(frozen=True)
class RiskScenarioReport:
    base_snapshot: PortfolioRiskSnapshot
    results: Tuple[RiskScenarioResult, ...]
    worst_case_by_pv: RiskScenarioResult
    best_case_by_pv: RiskScenarioResult
    max_loss: float
    max_gain: float
    risk_context: RiskContext | None = None


def _greeks_diff(a: Greeks, b: Greeks) -> Greeks:
    return Greeks(delta=a.delta - b.delta, gamma=a.gamma - b.gamma, vega=a.vega - b.vega, theta=a.theta - b.theta, rho=a.rho - b.rho)


from core.risk.semantics import RiskContext, default_risk_context

def build_risk_scenario_report(
    state: PortfolioState,
    base_ctx: PricingContext,
    pricing_engine: PricingEngine,
    scenarios: ScenarioSet,
    risk_context: RiskContext | None = None,
) -> RiskScenarioReport:
    # Base valuation
    base_currency = base_ctx.base_currency
    base_positions = valuate_and_risk_positions(state=state, pricing_engine=pricing_engine, snapshot=base_ctx.market, base_currency=base_currency, context=base_ctx)
    base_agg = aggregate_portfolio_risk(base_positions, base_currency=base_currency)
    base_total = float(base_agg.total_pv)

    results_list: list[RiskScenarioResult] = []

    for sc in scenarios.scenarios:
        shocked_pricing_ctx = build_shocked_context(base_ctx, sc)
        sc_positions = valuate_and_risk_positions(state=state, pricing_engine=pricing_engine, snapshot=shocked_pricing_ctx.market, base_currency=base_currency, context=shocked_pricing_ctx)
        sc_agg = aggregate_portfolio_risk(sc_positions, base_currency=base_currency)
        sc_total = float(sc_agg.total_pv)

        delta_abs = sc_total - base_total
        delta_pct = (delta_abs / base_total) if base_total != 0.0 else 0.0

        # build per-symbol maps (by position key)
        base_map = {p.key: p for p in base_positions}
        sc_map = {p.key: p for p in sc_positions}

        keys = sorted(set(base_map.keys()) | set(sc_map.keys()))

        # compute per-symbol delta pv and greeks
        pv_list: list[tuple[str, float]] = []
        greeks_list: list[tuple[str, Greeks]] = []
        for k in keys:
            base_pr = base_map.get(k)
            sc_pr = sc_map.get(k)
            base_pv = float(base_pr.pv) if base_pr is not None else 0.0
            sc_pv = float(sc_pr.pv) if sc_pr is not None else 0.0
            pv_list.append((k, sc_pv - base_pv))

            base_g = base_pr.greeks if base_pr is not None else Greeks(0.0, 0.0, 0.0, 0.0, 0.0)
            sc_g = sc_pr.greeks if sc_pr is not None else Greeks(0.0, 0.0, 0.0, 0.0, 0.0)
            diff = _greeks_diff(sc_g, base_g)
            greeks_list.append((k, diff))

        # ensure deterministic ordering
        per_symbol_delta_pv = tuple(sorted(pv_list, key=lambda kv: str(kv[0])))
        per_symbol_delta_greeks = tuple(sorted(greeks_list, key=lambda kv: str(kv[0])))

        rsr = RiskScenarioResult(
            scenario_name=sc.name,
            base_total_pv=base_total,
            scenario_total_pv=sc_total,
            delta_pv_abs=float(delta_abs),
            delta_pv_pct=float(delta_pct),
            per_symbol_delta_pv=per_symbol_delta_pv,
            per_symbol_delta_greeks=per_symbol_delta_greeks,
        )
        results_list.append(rsr)

    # sort results deterministically by scenario name
    results = tuple(sorted(results_list, key=lambda r: r.scenario_name))

    # determine worst/best by scenario_total_pv (worst = minimal total pv)
    worst = min(results, key=lambda r: r.scenario_total_pv)
    best = max(results, key=lambda r: r.scenario_total_pv)

    max_loss = float(base_total - worst.scenario_total_pv)
    max_gain = float(best.scenario_total_pv - base_total)

    pricing_ctx: PricingContext = base_ctx  # for clarity, if needed for future use
    ctx: RiskContext = risk_context or default_risk_context()
    return RiskScenarioReport(
        base_snapshot=base_agg,
        results=results,
        worst_case_by_pv=worst,
        best_case_by_pv=best,
        max_loss=max_loss,
        max_gain=max_gain,
        risk_context=ctx,
    )


__all__ = ["RiskScenarioResult", "RiskScenarioReport", "build_risk_scenario_report"]
