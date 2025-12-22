from __future__ import annotations

from core.backtest import TimePoint, BacktestTimeline, BacktestEngine
from core.market_data.types import MarketSnapshot, PriceQuote
from core.pricing.simple import SimpleSpotPricingEngine
from core.pricing.types import PricingError
from core.arbitrage.models import ArbitrageOpportunity, ArbitrageLeg


def _make_opportunity(symbol: str, size: float) -> ArbitrageOpportunity:
    buy = ArbitrageLeg(action="buy", venue="X", price=0.0, quantity=size)
    sell = ArbitrageLeg(action="sell", venue="Y", price=0.0, quantity=size)
    return ArbitrageOpportunity(symbol=symbol, buy=buy, sell=sell, gross_edge=0.0, net_edge=0.0, edge_bps=0.0, size=size)


def test_successful_replay_and_final_price():
    engine = SimpleSpotPricingEngine()
    op = _make_opportunity("TICK", 1.0)

    s1 = MarketSnapshot(quotes=(PriceQuote(asset="TICK", price=1.0, currency="USD"),), fx_rates=(), as_of="t1")
    s2 = MarketSnapshot(quotes=(PriceQuote(asset="TICK", price=2.0, currency="USD"),), fx_rates=(), as_of="t2")

    tp1 = TimePoint(t=1, snapshot=s1)
    tp2 = TimePoint(t=2, snapshot=s2)
    timeline = BacktestTimeline(points=(tp1, tp2))

    res = BacktestEngine.run_backtest(op, timeline, engine, base_currency="USD")
    assert len(res.steps) == 2
    assert res.final_price.pv == 2.0


def test_determinism_with_shuffled_input():
    engine = SimpleSpotPricingEngine()
    op = _make_opportunity("X", 1.0)

    s1 = MarketSnapshot(quotes=(PriceQuote(asset="X", price=5.0, currency="USD"),), fx_rates=(), as_of="a")
    s2 = MarketSnapshot(quotes=(PriceQuote(asset="X", price=6.0, currency="USD"),), fx_rates=(), as_of="b")

    tp1 = TimePoint(t="a", snapshot=s1)
    tp2 = TimePoint(t="b", snapshot=s2)

    # shuffled input
    timeline1 = BacktestTimeline(points=(tp2, tp1))
    timeline2 = BacktestTimeline(points=(tp1, tp2))

    r1 = BacktestEngine.run_backtest(op, timeline1, engine)
    r2 = BacktestEngine.run_backtest(op, timeline2, engine)

    assert tuple(step.price.pv for step in r1.steps) == tuple(step.price.pv for step in r2.steps)


def test_missing_price_raises():
    engine = SimpleSpotPricingEngine()
    op = _make_opportunity("M", 1.0)
    s1 = MarketSnapshot(quotes=(), fx_rates=(), as_of="t1")
    tp1 = TimePoint(t=1, snapshot=s1)
    timeline = BacktestTimeline(points=(tp1,))

    try:
        BacktestEngine.run_backtest(op, timeline, engine)
        assert False, "expected PricingError"
    except PricingError:
        pass
