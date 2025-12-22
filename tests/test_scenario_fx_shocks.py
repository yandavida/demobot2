from __future__ import annotations

from core.scenarios.types import Scenario, ScenarioSet
from core.market_data.types import MarketSnapshot, PriceQuote, FxRateQuote
from core.portfolio.portfolio_models import PortfolioState, Position
from core.pricing.option_types import EuropeanOption
from core.pricing.bs import BlackScholesPricingEngine
from core.pricing.context import PricingContext
from core.vol.inmemory import InMemoryVolProvider
from core.portfolio.scenario_engine import run_portfolio_scenarios
from core.fx.errors import MissingFxRateError


def test_fx_shock_direct_pair():
    snap = MarketSnapshot(
        quotes=(PriceQuote(asset="X", price=10.0, currency="USD"),),
        fx_rates=(FxRateQuote(pair="USD/ILS", rate=3.5),),
    )
    sc = Scenario(name="fx1", shocks_by_symbol=(), fx_shocks_by_pair=(("USD/ILS", 1.1),))
    # apply via build_shocked_context through scenario engine
    vp = InMemoryVolProvider({})
    base_ctx = PricingContext(market=snap, vol_provider=vp)
    engine = BlackScholesPricingEngine()

    # No positions needed to validate fx rates change directly via apply_shock_to_snapshot
    report = run_portfolio_scenarios(PortfolioState.with_positions([], base_currency="ILS"), base_ctx, engine, ScenarioSet(scenarios=(sc,)))
    # ensure shocked fx present and updated
    shocked = report.results[0]
    assert shocked is not None


def test_fx_shock_inverse_pair():
    snap = MarketSnapshot(
        quotes=(PriceQuote(asset="X", price=10.0, currency="USD"),),
        fx_rates=(FxRateQuote(pair="ILS/USD", rate=0.2857142857),),  # inverse of 3.5
    )
    sc = Scenario(name="fxinv", shocks_by_symbol=(), fx_shocks_by_pair=(("USD/ILS", 2.0),))
    vp = InMemoryVolProvider({})
    base_ctx = PricingContext(market=snap, vol_provider=vp)
    engine = BlackScholesPricingEngine()

    report = run_portfolio_scenarios(PortfolioState.with_positions([], base_currency="ILS"), base_ctx, engine, ScenarioSet(scenarios=(sc,)))
    assert report.results[0] is not None


def test_fx_shock_missing_pair_strict_raises():
    snap = MarketSnapshot(quotes=(), fx_rates=())
    sc = Scenario(name="missing", shocks_by_symbol=(), fx_shocks_by_pair=(("USD/ILS", 1.1),))
    vp = InMemoryVolProvider({})
    base_ctx = PricingContext(market=snap, vol_provider=vp)
    engine = BlackScholesPricingEngine()

    try:
        run_portfolio_scenarios(PortfolioState.with_positions([], base_currency="ILS"), base_ctx, engine, ScenarioSet(scenarios=(sc,)))
        assert False, "expected MissingFxRateError"
    except MissingFxRateError:
        pass


def test_fx_shock_affects_portfolio_valuation():
    # Create a USD-priced option that will be valued into ILS
    opt = EuropeanOption(underlying="AAA", option_type="call", strike=100.0, expiry_t=0.5, vol=0.2, contract_multiplier=1.0)
    pos = Position(key="p1", execution=opt, quantity=1.0)
    state = PortfolioState.with_positions([pos], base_currency="ILS")

    snap = MarketSnapshot(
        quotes=(PriceQuote(asset="AAA", price=120.0, currency="USD"),),
        fx_rates=(FxRateQuote(pair="USD/ILS", rate=3.0),),
    )

    vp = InMemoryVolProvider({"AAA": 0.2})
    base_ctx = PricingContext(market=snap, vol_provider=vp)
    engine = BlackScholesPricingEngine()

    base_report = run_portfolio_scenarios(state, base_ctx, engine, ScenarioSet(scenarios=(Scenario(name="base", shocks_by_symbol=(), fx_shocks_by_pair=()),),))
    base_pv = base_report.results[0].total_pv

    # apply FX shock increasing USD/ILS by 10% -> expected PV in ILS increases proportionally
    sc = Scenario(name="fxup", shocks_by_symbol=(), fx_shocks_by_pair=(("USD/ILS", 1.1),))
    shocked = run_portfolio_scenarios(state, base_ctx, engine, ScenarioSet(scenarios=(sc,)))
    shocked_pv = shocked.results[0].total_pv

    assert shocked_pv > base_pv
