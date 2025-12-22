from core.portfolio.portfolio_models import Position, PortfolioState
from core.portfolio.constraints import (
    ConstraintSpec,
    evaluate_constraints,
    PortfolioConstraintError,
)
from core.arbitrage.models import ArbitrageOpportunity, ArbitrageLeg


class EconStub:
    def __init__(self, exposure_by_currency=None, cash_usage=None, exposure_by_asset=None):
        self.exposure_by_currency = exposure_by_currency or {}
        self.cash_usage = cash_usage or {}
        self.exposure_by_asset = exposure_by_asset or {}


def _make_exec(id: str, econ=None):
    buy = ArbitrageLeg(action="buy", venue="V", price=100.0, quantity=1.0)
    sell = ArbitrageLeg(action="sell", venue="W", price=101.0, quantity=1.0)
    opp = ArbitrageOpportunity(symbol="S", buy=buy, sell=sell, gross_edge=1.0, net_edge=1.0, edge_bps=100.0, size=1.0, ccy="USD", notes=[], opportunity_id=id)
    if econ is not None:
        setattr(opp, "economics", econ)
    return opp


def test_non_strict_violations_reported():
    e1 = EconStub(exposure_by_currency={"USD": 500.0}, cash_usage={"USD": 400.0})
    exec1 = _make_exec("p1", econ=e1)
    p1 = Position(key="p1", execution=exec1, quantity=1.0)
    state = PortfolioState.with_positions([p1], bump_revision=False)

    specs = [
        ConstraintSpec(name="pos_limit", kind="max_position_count", limits={"*": 0}),
        ConstraintSpec(name="cash_limit", kind="max_cash_usage_by_ccy", limits={"USD": 100.0}),
        ConstraintSpec(name="exp_limit", kind="max_gross_exposure_by_ccy", limits={"USD": 100.0}),
    ]

    report = evaluate_constraints(state, specs, strict=False)
    assert report.ok is False
    assert report.violation_count >= 1


def test_strict_mode_raises():
    e1 = EconStub(exposure_by_currency={"USD": 500.0}, cash_usage={"USD": 400.0})
    exec1 = _make_exec("p1", econ=e1)
    p1 = Position(key="p1", execution=exec1, quantity=1.0)
    state = PortfolioState.with_positions([p1], bump_revision=False)

    specs = [
        ConstraintSpec(name="cash_limit", kind="max_cash_usage_by_ccy", limits={"USD": 100.0}, strict=True),
    ]

    try:
        evaluate_constraints(state, specs)
        assert False, "expected PortfolioConstraintError"
    except PortfolioConstraintError as exc:
        rep = exc.report
        assert rep.violation_count >= 1


def test_deterministic_ordering_of_violations():
    e1 = EconStub(exposure_by_currency={"USD": 500.0, "ILS": 200.0}, cash_usage={"USD": 400.0, "ILS": 50.0})
    exec1 = _make_exec("p1", econ=e1)
    p1 = Position(key="p1", execution=exec1, quantity=1.0)
    state = PortfolioState.with_positions([p1], bump_revision=False)

    specs_a = [
        ConstraintSpec(name="a", kind="max_cash_usage_by_ccy", limits={"USD": 100.0}),
        ConstraintSpec(name="b", kind="max_gross_exposure_by_ccy", limits={"USD": 100.0}),
    ]

    specs_b = list(reversed(specs_a))

    r1 = evaluate_constraints(state, specs_a, strict=False)
    r2 = evaluate_constraints(state, specs_b, strict=False)

    assert tuple(v.key for v in r1.violations) == tuple(v.key for v in r2.violations)
