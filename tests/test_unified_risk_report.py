from core.risk.unified_report import build_unified_portfolio_risk_report
from core.risk.unified_report_types import UnifiedPortfolioRiskReport
from core.scenarios.types import Scenario, ScenarioSet, Shock
from core.pricing.context import PricingContext
from core.pricing.bs import BlackScholesPricingEngine
from core.market_data.types import MarketSnapshot, PriceQuote, FxRateQuote
from core.vol.inmemory import InMemoryVolProvider
from core.portfolio.portfolio_models import PortfolioState, Position
from core.pricing.option_types import EuropeanOption
import pytest

def make_tiny_state_and_ctx():
    opt = EuropeanOption(underlying="AAA", option_type="call", strike=100.0, expiry_t=0.5, vol=0.2, contract_multiplier=1.0)
    pos = Position(key="p1", execution=opt, quantity=1.0)
    state = PortfolioState.with_positions([pos], base_currency="USD")
    snap = MarketSnapshot(quotes=(PriceQuote(asset="AAA", price=120.0, currency="USD"),), fx_rates=(FxRateQuote(pair="USD/ILS", rate=3.0),))
    vp = InMemoryVolProvider({"AAA": 0.2})
    base_ctx = PricingContext(market=snap, vol_provider=vp, fx_converter=None, base_currency="USD")
    engine = BlackScholesPricingEngine()
    # Build 21 deterministic scenarios: -0.10, ..., -0.01, 0.0, +0.01, ..., +0.10
    symbol = "AAA"
    spot_grid = [-(i / 100.0) for i in range(10, 0, -1)] + [0.0] + [(i / 100.0) for i in range(1, 11)]
    scenarios = [
        Scenario(
            name=f"spot_{pct:+.2%}",
            shocks_by_symbol=((symbol, Shock(spot_pct=pct)),),
            fx_shocks_by_pair=()
        )
        for pct in spot_grid
    ]
    sset = ScenarioSet(scenarios=tuple(scenarios))
    return state, base_ctx, engine, sset

def test_unified_report_basic():
    state, base_ctx, engine, sset = make_tiny_state_and_ctx()
    report = build_unified_portfolio_risk_report(
        state=state,
        base_ctx=base_ctx,
        pricing_engine=engine,
        scenarios=sset,
    )
    assert isinstance(report, UnifiedPortfolioRiskReport)
    assert report.base_snapshot is not None
    assert report.scenario_report is not None
    assert report.risk_context is not None
    assert report.historical_var is not None
    assert report.historical_var.var >= 0
    assert report.historical_var.cvar is None or report.historical_var.cvar >= report.historical_var.var

def test_unified_report_determinism():
    state, base_ctx, engine, sset = make_tiny_state_and_ctx()
    report1 = build_unified_portfolio_risk_report(
        state=state,
        base_ctx=base_ctx,
        pricing_engine=engine,
        scenarios=sset,
    )
    report2 = build_unified_portfolio_risk_report(
        state=state,
        base_ctx=base_ctx,
        pricing_engine=engine,
        scenarios=sset,
    )
    # scenario_report.results ordering
    res1 = [r.scenario_name for r in report1.scenario_report.results]
    res2 = [r.scenario_name for r in report2.scenario_report.results]
    assert res1 == res2
    # VaR/CVaR numeric equality
    assert report1.historical_var.var == pytest.approx(report2.historical_var.var, rel=1e-12)
    assert report1.historical_var.cvar == report2.historical_var.cvar
