from __future__ import annotations

from core.backtest import TimePoint, BacktestTimeline
from core.backtest.portfolio import run_portfolio_backtest
from core.market_data.types import MarketSnapshot, PriceQuote
from core.pricing.simple import SimpleSpotPricingEngine
from core.pricing.types import PricingError
from core.portfolio.portfolio_models import Position
from core.portfolio.wiring import PortfolioCandidate
from core.portfolio.constraints import ConstraintSpec
# no-op


class ExecStub:
    def __init__(self, opportunity_id: str, asset: str, economics: object | None = None) -> None:
        self.opportunity_id = opportunity_id
        self.symbol = asset
        self.economics = economics

    def __str__(self) -> str:
        return f"ExecStub({self.opportunity_id})"


def _make_position(key: str, exec: ExecStub, qty: float) -> Position:
    return Position(key=key, execution=exec, quantity=qty)


def test_successful_portfolio_backtest_and_totals():
    # two positions with different quantities
    e1 = ExecStub("p1", "A")
    e2 = ExecStub("p2", "B")
    pos1 = _make_position("p1", e1, 2.0)
    pos2 = _make_position("p2", e2, 3.0)
    cand = PortfolioCandidate(positions=(pos1, pos2), name="c")

    # timeline snapshots
    s1 = MarketSnapshot(quotes=(PriceQuote(asset="A", price=1.0, currency="USD"), PriceQuote(asset="B", price=2.0, currency="USD")), fx_rates=(), as_of="t1")
    s2 = MarketSnapshot(quotes=(PriceQuote(asset="A", price=2.0, currency="USD"), PriceQuote(asset="B", price=3.0, currency="USD")), fx_rates=(), as_of="t2")

    tp1 = TimePoint(t=1, snapshot=s1)
    tp2 = TimePoint(t=2, snapshot=s2)
    timeline = BacktestTimeline(points=(tp1, tp2))

    engine = SimpleSpotPricingEngine()

    res = run_portfolio_backtest(cand, timeline, engine, constraint_specs=[])
    assert len(res.steps) == 2
    # total pv at t1 = 1*2 + 2*3 = 8
    assert res.steps[0].total_pv == 8.0
    # total pv at t2 = 2*2 + 3*3 = 13
    assert res.steps[1].total_pv == 13.0


def test_determinism_with_shuffled_timeline():
    e1 = ExecStub("p1", "Z")
    pos1 = _make_position("p1", e1, 1.0)
    cand = PortfolioCandidate(positions=(pos1,), name="x")

    s1 = MarketSnapshot(quotes=(PriceQuote(asset="Z", price=5.0, currency="USD"),), fx_rates=(), as_of="a")
    s2 = MarketSnapshot(quotes=(PriceQuote(asset="Z", price=6.0, currency="USD"),), fx_rates=(), as_of="b")

    tp1 = TimePoint(t="a", snapshot=s1)
    tp2 = TimePoint(t="b", snapshot=s2)

    t1 = BacktestTimeline(points=(tp2, tp1))
    t2 = BacktestTimeline(points=(tp1, tp2))

    engine = SimpleSpotPricingEngine()
    r1 = run_portfolio_backtest(cand, t1, engine, constraint_specs=[])
    r2 = run_portfolio_backtest(cand, t2, engine, constraint_specs=[])

    assert tuple(step.total_pv for step in r1.steps) == tuple(step.total_pv for step in r2.steps)


def test_missing_price_raises_pricingerror():
    e1 = ExecStub("p1", "MISSING")
    pos1 = _make_position("p1", e1, 1.0)
    cand = PortfolioCandidate(positions=(pos1,), name="m")

    s1 = MarketSnapshot(quotes=(), fx_rates=(), as_of="t1")
    tp1 = TimePoint(t=1, snapshot=s1)
    timeline = BacktestTimeline(points=(tp1,))

    engine = SimpleSpotPricingEngine()
    try:
        run_portfolio_backtest(cand, timeline, engine, constraint_specs=[])
        assert False, "expected PricingError"
    except PricingError:
        pass


def test_constraints_integration_and_strict_mode():
    e1 = ExecStub("p1", "A")
    e2 = ExecStub("p2", "B")
    pos1 = _make_position("p1", e1, 1.0)
    pos2 = _make_position("p2", e2, 1.0)
    cand = PortfolioCandidate(positions=(pos1, pos2), name="c")

    s = MarketSnapshot(quotes=(PriceQuote(asset="A", price=1.0, currency="USD"), PriceQuote(asset="B", price=1.0, currency="USD")), fx_rates=(), as_of="t")
    tp = TimePoint(t=1, snapshot=s)
    timeline = BacktestTimeline(points=(tp,))

    # spec limiting positions to 1 should violate
    spec = ConstraintSpec(name="limit0", kind="max_position_count", limits={"*": 1}, strict=True)

    engine = SimpleSpotPricingEngine()
    res = run_portfolio_backtest(cand, timeline, engine, constraint_specs=[spec], strict_constraints=True)
    assert res.steps[0].constraints.ok is False
    assert any(w.startswith("constraint_violations:") for w in res.steps[0].warnings)
