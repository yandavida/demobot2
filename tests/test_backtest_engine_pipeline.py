from core.backtest import TimePoint, BacktestTimeline, BacktestEngine
from core.market_data.types import MarketSnapshot, PriceQuote
from core.pricing.simple import SimpleSpotPricingEngine
from core.arbitrage.models import ArbitrageOpportunity, ArbitrageLeg
import pytest

def _make_opportunity(symbol: str, size: float) -> ArbitrageOpportunity:
    buy = ArbitrageLeg(action="buy", venue="X", price=0.0, quantity=size)
    sell = ArbitrageLeg(action="sell", venue="Y", price=0.0, quantity=size)
    return ArbitrageOpportunity(symbol=symbol, buy=buy, sell=sell, gross_edge=0.0, net_edge=0.0, edge_bps=0.0, size=size)

def test_backtest_engine_runs_one_step_per_timepoint(monkeypatch):
    from core.backtest.engine import BacktestEngine
    engine = SimpleSpotPricingEngine()
    op = _make_opportunity("TICK", 1.0)
    s1 = MarketSnapshot(quotes=(PriceQuote(asset="TICK", price=1.0, currency="USD"),), fx_rates=(), as_of="t1")
    s2 = MarketSnapshot(quotes=(PriceQuote(asset="TICK", price=2.0, currency="USD"),), fx_rates=(), as_of="t2")
    tp1 = TimePoint(t=1, snapshot=s1)
    tp2 = TimePoint(t=2, snapshot=s2)
    timeline = BacktestTimeline(points=(tp1, tp2))
    calls = []
    orig = BacktestEngine._run_step
    def wrapped(self, tp, *args, **kwargs):
        calls.append(tp.t)
        return orig(self, tp, *args, **kwargs)
    monkeypatch.setattr(BacktestEngine, "_run_step", wrapped)
    res = BacktestEngine.run_backtest(op, timeline, engine, base_currency="USD")
    assert len(res.steps) == len(calls)
    assert len(calls) == len(timeline.points)
