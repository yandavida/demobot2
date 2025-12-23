from __future__ import annotations
from datetime import datetime
from core.risk.unified_report_types import UnifiedPortfolioRiskReport
from core.scenarios.risk_report import build_risk_scenario_report
from core.risk.var_historical import calc_historical_var, calc_cvar_expected_shortfall
from core.risk.var_types import VarResult
from core.risk.semantics import RiskContext, default_risk_context

# imports for type hints
from core.portfolio.portfolio_models import PortfolioState
from core.pricing.context import PricingContext
from core.pricing.engine import PricingEngine
from core.scenarios.types import ScenarioSet


def build_unified_portfolio_risk_report(
    *,
    state: PortfolioState,
    base_ctx: PricingContext,
    pricing_engine: PricingEngine,
    scenarios: ScenarioSet,
    risk_context: RiskContext | None = None,
    risk_assumptions = None,
) -> UnifiedPortfolioRiskReport:
    ctx = risk_context or default_risk_context()
    scenario_report = build_risk_scenario_report(
        state=state,
        base_ctx=base_ctx,
        pricing_engine=pricing_engine,
        scenarios=scenarios,
        risk_context=ctx,
    )
    pnl_series = [r.delta_pv_abs for r in scenario_report.results]
    var_value = calc_historical_var(pnl_series=pnl_series, confidence=ctx.confidence)
    cvar_value = calc_cvar_expected_shortfall(pnl_series=pnl_series, confidence=ctx.confidence)
    var_result = VarResult(
        method="historical",
        confidence=ctx.confidence,
        horizon_days=ctx.horizon_days,
        currency=ctx.base_currency,
        var=var_value,
        cvar=cvar_value,
        notes={},
    )
    return UnifiedPortfolioRiskReport(
        created_at=datetime.utcnow(),
        base_snapshot=scenario_report.base_snapshot,
        scenario_report=scenario_report,
        historical_var=var_result,
        historical_cvar=cvar_value,
        notes={},
        risk_context=ctx,
        risk_assumptions=risk_assumptions,
    )
