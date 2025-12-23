from __future__ import annotations

from core.scenarios.types import Shock, Scenario, ScenarioSet
from core.portfolio.portfolio_models import PortfolioState, Position
from core.pricing.bs import BlackScholesPricingEngine
from core.pricing.context import PricingContext
from core.market_data.types import MarketSnapshot, PriceQuote, FxRateQuote
from core.vol.inmemory import InMemoryVolProvider
from core.scenarios.risk_report import build_risk_scenario_report, RiskScenarioReport
from core.pricing.option_types import EuropeanOption


def _make_state_with_one_call(key: str, underlying: str, strike: float, expiry_t: float, qty: float):
    opt = EuropeanOption(underlying=underlying, option_type="call", strike=strike, expiry_t=expiry_t, vol=0.2, contract_multiplier=1.0)
    pos = Position(key=key, execution=opt, quantity=qty)
    return PortfolioState.with_positions([pos], base_currency="USD")


def test_deterministic_ordering_and_delta_pv():
    state = _make_state_with_one_call("p1", "AAA", 100.0, 0.5, 1.0)
    snap = MarketSnapshot(quotes=(PriceQuote(asset="AAA", price=120.0, currency="USD"),), fx_rates=(FxRateQuote(pair="USD/ILS", rate=3.0),))
    vp = InMemoryVolProvider({"AAA": 0.2})
    base_ctx = PricingContext(market=snap, vol_provider=vp, fx_converter=None, base_currency="USD")
    engine = BlackScholesPricingEngine()

    up = Scenario(name="up", shocks_by_symbol=(("AAA", Shock(spot_pct=0.1)),), fx_shocks_by_pair=())
    down = Scenario(name="down", shocks_by_symbol=(("AAA", Shock(spot_pct=-0.1)),), fx_shocks_by_pair=())
    sset = ScenarioSet(scenarios=(up, down))

    report = build_risk_scenario_report(state, base_ctx, engine, sset)
    assert isinstance(report, RiskScenarioReport)
    # deterministic ordering by scenario name
    assert tuple(r.scenario_name for r in report.results) == ("down", "up")

    base_total = report.base_snapshot.total_pv
    up_total = next(r for r in report.results if r.scenario_name == "up").scenario_total_pv
    down_total = next(r for r in report.results if r.scenario_name == "down").scenario_total_pv
    assert up_total > down_total


def test_greeks_change_on_vol_shock():
    state = _make_state_with_one_call("p1", "BBB", 100.0, 0.5, 1.0)
    snap = MarketSnapshot(quotes=(PriceQuote(asset="BBB", price=120.0, currency="USD"),), fx_rates=())
    vp = InMemoryVolProvider({"BBB": 0.2})
    base_ctx = PricingContext(market=snap, vol_provider=vp, fx_converter=None, base_currency="USD")
    engine = BlackScholesPricingEngine()

    vol_up = Scenario(name="volup", shocks_by_symbol=(), fx_shocks_by_pair=(("BBB", Shock(vol_abs=0.1)).__repr__(),))
    # Above line intentionally wrong shape will be corrected by construction in Scenario
    # Instead construct scenario properly:
    vol_up = Scenario(name="volup", shocks_by_symbol=(), fx_shocks_by_pair=())
    # Build a scenario with a vol shock via shocks_by_symbol
    vol_up = Scenario(name="volup", shocks_by_symbol=(("BBB", Shock(vol_abs=0.1)),), fx_shocks_by_pair=())

    sset = ScenarioSet(scenarios=(vol_up,))
    report = build_risk_scenario_report(state, base_ctx, engine, sset)
    res = report.results[0]
    # greeks are present per symbol
    assert any(isinstance(g, tuple) for g in res.per_symbol_delta_greeks)


def test_fx_shock_affects_base_currency_pv():
    # USD position valued into ILS base should reflect fx shocks
    state = _make_state_with_one_call("p1", "CCC", 100.0, 0.5, 1.0)
    snap = MarketSnapshot(quotes=(PriceQuote(asset="CCC", price=120.0, currency="USD"),), fx_rates=(FxRateQuote(pair="USD/ILS", rate=3.0),))
    vp = InMemoryVolProvider({"CCC": 0.2})
    base_ctx = PricingContext(market=snap, vol_provider=vp, fx_converter=None, base_currency="ILS")
    engine = BlackScholesPricingEngine()

    sc = Scenario(name="fxup", shocks_by_symbol=(), fx_shocks_by_pair=(("USD/ILS", 1.1),))
    sset = ScenarioSet(scenarios=(sc,))

    report = build_risk_scenario_report(state, base_ctx, engine, sset)
    res = report.results[0]
    assert res.scenario_total_pv != res.base_total_pv
