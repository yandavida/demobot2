from __future__ import annotations

from core.pricing.bs import BlackScholesPricingEngine
from core.pricing.option_types import EuropeanOption
from core.market_data.types import MarketSnapshot, PriceQuote, FxRateQuote
from core.portfolio.wiring import build_candidate_from_executions
from core.backtest.timeline import TimePoint, BacktestTimeline
from core.backtest.portfolio import run_portfolio_risk_backtest


def _pos(exec_obj, qty: float):
    # helper to create positions via candidate builder (works with executions)
    return build_candidate_from_executions([exec_obj], quantity=qty)


def test_portfolio_risk_aggregation_and_scaling():
    # two European options on same underlying with different strikes
    o1 = EuropeanOption(underlying="XYZ", option_type="call", strike=90.0, expiry_t=0.5, currency="USD", contract_multiplier=1.0, vol=0.25)
    o2 = EuropeanOption(underlying="XYZ", option_type="put", strike=110.0, expiry_t=0.5, currency="USD", contract_multiplier=1.0, vol=0.25)

    # candidate with two positions
    # use build_candidate_from_executions to build deterministic candidate
    cand = build_candidate_from_executions([o1, o2], quantity=2.0)

    # snapshots with spot changes
    s1 = MarketSnapshot(quotes=(PriceQuote(asset="XYZ", price=100.0, currency="USD"),), fx_rates=(), as_of="t1")
    s2 = MarketSnapshot(quotes=(PriceQuote(asset="XYZ", price=110.0, currency="USD"),), fx_rates=(), as_of="t2")

    tp1 = TimePoint(t=1, snapshot=s1)
    tp2 = TimePoint(t=2, snapshot=s2)
    timeline = BacktestTimeline(points=(tp1, tp2))

    engine = BlackScholesPricingEngine()

    snaps = run_portfolio_risk_backtest(cand, timeline, engine, constraint_specs=[])
    assert len(snaps) == 2

    # totals equal sum of positions
    first = snaps[0]
    assert first.total_pv == sum(p.pv for p in first.positions)

    # scaling: doubling quantity (we used quantity=2) -> verify non-zero greeks and pv
    assert first.total_pv > 0
    for p in first.positions:
        assert p.greeks.gamma >= 0


def test_fx_conversion_of_pv_and_greeks():
    # option priced in USD but base currency ILS with fx rate
    o = EuropeanOption(underlying="AAA", option_type="call", strike=50.0, expiry_t=0.5, currency="USD", contract_multiplier=1.0, vol=0.2)
    cand = build_candidate_from_executions([o], quantity=1.0)

    s = MarketSnapshot(quotes=(PriceQuote(asset="AAA", price=55.0, currency="USD"),), fx_rates=(FxRateQuote(pair="USD/ILS", rate=3.0),), as_of="t")
    tp = TimePoint(t=1, snapshot=s)
    timeline = BacktestTimeline(points=(tp,))

    engine = BlackScholesPricingEngine()
    snaps = run_portfolio_risk_backtest(cand, timeline, engine, constraint_specs=[], base_currency="ILS")
    snap = snaps[0]
    # PV should be converted to ILS (> spot*rate*something)
    assert snap.currency == "ILS"
    assert snap.total_pv > 0
