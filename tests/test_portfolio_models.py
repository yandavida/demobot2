from core.portfolio.portfolio_models import (
    Position,
    PortfolioState,
    build_portfolio_snapshot,
    PortfolioTotals,
)
from core.arbitrage.models import ArbitrageOpportunity, ArbitrageLeg
import pytest


def _make_exec(id: str, buy_p: float = 100.0, sell_p: float = 101.0, size: float = 1.0):
    buy = ArbitrageLeg(action="buy", venue="V", price=buy_p, quantity=size)
    sell = ArbitrageLeg(action="sell", venue="W", price=sell_p, quantity=size)
    return ArbitrageOpportunity(symbol="S", buy=buy, sell=sell, gross_edge=(sell_p - buy_p), net_edge=(sell_p - buy_p), edge_bps=((sell_p - buy_p) / buy_p) * 10_000, size=size, ccy="USD", notes=[], opportunity_id=id)


def test_position_quantity_positive():
    exec = _make_exec("x")
    with pytest.raises(ValueError):
        Position(key="x", execution=exec, quantity=0.0)


def test_portfoliostate_positions_tuple_and_sorting():
    a = _make_exec("a")
    b = _make_exec("b")
    p1 = Position(key="b", execution=b, quantity=1.0)
    p2 = Position(key="a", execution=a, quantity=2.0)
    state = PortfolioState.with_positions([p1, p2], bump_revision=False)
    # positions stored as tuple
    assert isinstance(state.positions, tuple)
    # sorted by key deterministically -> a then b
    assert state.positions[0].key == "a"


def test_revision_bump_and_add_remove_get():
    a = _make_exec("a")
    p = Position(key="a", execution=a, quantity=1.0)
    state = PortfolioState.with_positions([], bump_revision=False)
    s2 = state.add(p, bump_revision=True)
    assert s2.revision == state.revision + 1
    # get position
    assert s2.get_position("a") is not None
    # remove
    s3 = s2.remove_by_key("a", bump_revision=True)
    assert s3.get_position("a") is None


def test_build_snapshot_totals():
    a = _make_exec("a", size=2.0)
    b = _make_exec("b", size=3.0)
    p1 = Position(key="a", execution=a, quantity=2.0)
    p2 = Position(key="b", execution=b, quantity=3.0)
    state = PortfolioState.with_positions([p1, p2], bump_revision=False)
    snap = build_portfolio_snapshot(state)
    assert isinstance(snap.totals, PortfolioTotals)
    assert snap.totals.position_count == 2
    assert snap.totals.gross_quantity == pytest.approx(5.0)
