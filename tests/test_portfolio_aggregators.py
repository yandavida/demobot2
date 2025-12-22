from core.portfolio.portfolio_models import Position, PortfolioState
from core.portfolio.aggregators import aggregate_portfolio, validate_portfolio_economics_present
from core.arbitrage.models import ArbitrageLeg, ArbitrageOpportunity


class EconStub:
    def __init__(self, fees=0.0, slippage=0.0, notional=0.0, cash_usage=None, exposure_by_currency=None, exposure_by_asset=None):
        self.fees = fees
        self.slippage = slippage
        self.notional = notional
        self.cash_usage = cash_usage or {}
        self.exposure_by_currency = exposure_by_currency or {}
        self.exposure_by_asset = exposure_by_asset or {}


def _make_exec(id: str, buy_p=100.0, sell_p=101.0, size=1.0, econ=None):
    buy = ArbitrageLeg(action="buy", venue="V", price=buy_p, quantity=size)
    sell = ArbitrageLeg(action="sell", venue="W", price=sell_p, quantity=size)
    opp = ArbitrageOpportunity(symbol="S", buy=buy, sell=sell, gross_edge=(sell_p - buy_p), net_edge=(sell_p - buy_p), edge_bps=((sell_p - buy_p) / buy_p) * 10000, size=size, ccy="USD", notes=[], opportunity_id=id)
    if econ is not None:
        setattr(opp, "economics", econ)
    return opp


def test_aggregate_sums_and_exposure_merging():
    e1 = EconStub(fees=1.0, slippage=0.5, notional=100.0, exposure_by_currency={"USD": 100.0}, exposure_by_asset={"A": 50.0})
    e2 = EconStub(fees=2.0, slippage=1.0, notional=200.0, exposure_by_currency={"USD": 200.0, "ILS": 50.0}, exposure_by_asset={"A": 25.0, "B": 30.0})

    exec1 = _make_exec("p1", size=1.0, econ=e1)
    exec2 = _make_exec("p2", size=2.0, econ=e2)

    p1 = Position(key="p1", execution=exec1, quantity=1.0)
    p2 = Position(key="p2", execution=exec2, quantity=2.0)

    state = PortfolioState.with_positions([p1, p2], bump_revision=False)
    agg = aggregate_portfolio(state)

    assert agg.position_count == 2
    assert agg.gross_quantity == 3.0
    assert agg.total_fees == 3.0
    assert agg.total_slippage == 1.5
    assert agg.total_notional == 300.0
    # exposure_by_currency merged and sorted by key
    assert tuple(k for k, _ in agg.exposure_by_currency) == ("ILS", "USD")


def test_missing_economics_do_not_raise_and_validation_counts():
    exec_with = _make_exec("p1", econ=EconStub(fees=1.0))
    exec_without = _make_exec("p2", econ=None)

    p1 = Position(key="p1", execution=exec_with, quantity=1.0)
    p2 = Position(key="p2", execution=exec_without, quantity=1.0)
    state = PortfolioState.with_positions([p1, p2], bump_revision=False)

    agg = aggregate_portfolio(state)
    # missing economics contributes zero
    assert agg.total_fees == 1.0

    ok, missing = validate_portfolio_economics_present(state)
    assert ok is False
    assert missing == 1


def test_determinism_order_independence():
    e1 = EconStub(fees=1.0, exposure_by_currency={"USD": 100.0})
    e2 = EconStub(fees=2.0, exposure_by_currency={"USD": 200.0})
    exec1 = _make_exec("p1", econ=e1)
    exec2 = _make_exec("p2", econ=e2)
    p1 = Position(key="p1", execution=exec1, quantity=1.0)
    p2 = Position(key="p2", execution=exec2, quantity=1.0)

    s1 = PortfolioState.with_positions([p1, p2], bump_revision=False)
    s2 = PortfolioState.with_positions([p2, p1], bump_revision=False)

    a1 = aggregate_portfolio(s1)
    a2 = aggregate_portfolio(s2)
    assert a1.total_fees == a2.total_fees
    assert a1.exposure_by_currency == a2.exposure_by_currency
