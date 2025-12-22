from __future__ import annotations


from core.scenarios.types import Shock, Scenario, ScenarioSet
from core.portfolio.portfolio_models import PortfolioState, Position
from core.pricing.bs import BlackScholesPricingEngine
from core.pricing.context import PricingContext
from core.market_data.types import MarketSnapshot, PriceQuote
from core.vol.inmemory import InMemoryVolProvider
from core.portfolio.scenario_engine import run_portfolio_scenarios
from core.pricing.option_types import EuropeanOption


def _make_state_with_call(underlying: str, strike: float, expiry_t: float, qty: float):
    opt = EuropeanOption(underlying=underlying, option_type="call", strike=strike, expiry_t=expiry_t, vol=0.2, contract_multiplier=1.0)
    pos = Position(key=f"pos-{underlying}", execution=opt, quantity=qty)
    return PortfolioState.with_positions([pos], base_currency="USD")


def test_determinism_and_ordering():
    state = _make_state_with_call("FOO", 100.0, 0.5, 1.0)
    snap = MarketSnapshot(quotes=(PriceQuote(asset="FOO", price=100.0, currency="USD"),))
    vp = InMemoryVolProvider({"FOO": 0.2})
    base_ctx = PricingContext(market=snap, vol_provider=vp)
    engine = BlackScholesPricingEngine()

    sc1 = Scenario(name="s1", shocks_by_symbol=(("FOO", Shock(spot_pct=0.1)),))
    sc2 = Scenario(name="s2", shocks_by_symbol=(("FOO", Shock(spot_pct=-0.05)),))
    sset = ScenarioSet(scenarios=(sc2, sc1))

    r1 = run_portfolio_scenarios(state, base_ctx, engine, sset)
    r2 = run_portfolio_scenarios(state, base_ctx, engine, sset)
    assert r1.results == r2.results
    # ordering by name
    assert tuple(r.name for r in r1.results) == ("s1", "s2")


def test_bs_spot_and_vol_shock_effects():
    # Call should increase with positive spot shock
    state = _make_state_with_call("BAR", 100.0, 0.5, 1.0)
    snap = MarketSnapshot(quotes=(PriceQuote(asset="BAR", price=100.0, currency="USD"),))
    vp = InMemoryVolProvider({"BAR": 0.2})
    base_ctx = PricingContext(market=snap, vol_provider=vp)
    engine = BlackScholesPricingEngine()

    up = Scenario(name="up", shocks_by_symbol=(("BAR", Shock(spot_pct=0.1, vol_abs=0.0, vol_pct=0.0)),))
    down = Scenario(name="down", shocks_by_symbol=(("BAR", Shock(spot_pct=-0.1, vol_abs=0.0, vol_pct=0.0)),))
    sset = ScenarioSet(scenarios=(up, down))

    report = run_portfolio_scenarios(state, base_ctx, engine, sset)
    up_pv = next(r.total_pv for r in report.results if r.name == "up")
    down_pv = next(r.total_pv for r in report.results if r.name == "down")
    assert up_pv > down_pv

    # Vol shock increases PV for positive vega
    vol_up = Scenario(name="volup", shocks_by_symbol=(("BAR", Shock(vol_abs=0.1)),))
    report2 = run_portfolio_scenarios(state, base_ctx, engine, ScenarioSet(scenarios=(vol_up,)))
    vol_pv = report2.results[0].total_pv
    base_pv = run_portfolio_scenarios(state, base_ctx, engine, ScenarioSet(scenarios=(Scenario(name="base", shocks_by_symbol=()),))).results[0].total_pv
    assert vol_pv > base_pv
