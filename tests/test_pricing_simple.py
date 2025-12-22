from __future__ import annotations

from core.pricing import SimpleSpotPricingEngine, PricingContext, PriceResult, PricingError
from core.market_data.types import PriceQuote, MarketSnapshot
from core.arbitrage.models import ArbitrageOpportunity, ArbitrageLeg


def _make_opportunity(symbol: str, size: float) -> ArbitrageOpportunity:
    buy = ArbitrageLeg(action="buy", venue="X", price=0.0, quantity=size)
    sell = ArbitrageLeg(action="sell", venue="Y", price=0.0, quantity=size)
    return ArbitrageOpportunity(symbol=symbol, buy=buy, sell=sell, gross_edge=0.0, net_edge=0.0, edge_bps=0.0, size=size)


def test_successful_pricing_and_determinism():
    engine = SimpleSpotPricingEngine()
    q = PriceQuote(asset="AAPL", price=100.0, currency="USD")
    snap = MarketSnapshot(quotes=(q,), fx_rates=(), as_of="2025-01-01")
    ctx = PricingContext(market=snap, base_currency="USD")

    op = _make_opportunity("AAPL", 2.0)
    r1 = engine.price_execution(op, ctx)
    r2 = engine.price_execution(op, ctx)
    assert isinstance(r1, PriceResult)
    assert r1.pv == 100.0
    assert r1 == r2


def test_missing_price_raises():
    engine = SimpleSpotPricingEngine()
    snap = MarketSnapshot(quotes=(), fx_rates=(), as_of=None)
    ctx = PricingContext(market=snap, base_currency="USD")
    op = _make_opportunity("MISSING", 1.0)
    try:
        engine.price_execution(op, ctx)
        assert False, "expected PricingError"
    except PricingError:
        pass


def test_context_immutability():
    engine = SimpleSpotPricingEngine()
    q = PriceQuote(asset="SPX", price=10.0, currency="USD")
    snap = MarketSnapshot(quotes=(q,), fx_rates=(), as_of="2025-01-01")
    ctx = PricingContext(market=snap, base_currency="USD")
    op = _make_opportunity("SPX", 3.0)
    _ = engine.price_execution(op, ctx)
    # Ensure snapshot unchanged
    assert ctx.market.quotes[0].asset == "SPX"
