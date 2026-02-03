import math
from types import SimpleNamespace

from core.pnl.theoretical import compute_position_pnl, compute_portfolio_pnl
from core.pnl.portfolio_breakdown import compute_portfolio_pnl_breakdown
from core.numeric_policy import DEFAULT_TOLERANCES, MetricClass


def dummy_fx():
    class DummyFxConverter:
        def convert(self, amount: float, from_ccy, to_ccy, *, strict: bool = True) -> float:
            if from_ccy == to_ccy:
                return float(amount)
            # simple deterministic mapping for tests
            if from_ccy == "USD" and to_ccy == "ILS":
                return float(amount) * 4.0
            if from_ccy == "ILS" and to_ccy == "USD":
                return float(amount) / 4.0
            raise ValueError("Unsupported currency conversion")

    return DummyFxConverter()


def make_price(pv, ccy, breakdown=None):
    if breakdown is None:
        breakdown = {}
    return type("PriceResult", (), {"pv": pv, "currency": ccy, "breakdown": breakdown})()


def _close(a: float, b: float, metric: MetricClass) -> bool:
    tol = DEFAULT_TOLERANCES[metric]
    return math.isclose(a, b, rel_tol=tol.rel or 0.0, abs_tol=tol.abs or 0.0)


def test_aggregation_identity_and_pv_pnl_consistency():
    fx = dummy_fx()

    # Position 1
    pr1 = make_price(100.0, "USD", {"delta": 1.0})
    prev1 = make_price(90.0, "USD", {"delta": 1.0})
    pos1 = SimpleNamespace(id="p1", symbol="A", quantity=1.0)

    # Position 2 (different currency)
    pr2 = make_price(400.0, "ILS", {"delta": 0.5})
    prev2 = make_price(360.0, "ILS", {"delta": 0.5})
    pos2 = SimpleNamespace(id="p2", symbol="B", quantity=1.0)

    prev_results = {"p1": prev1, "p2": prev2}
    curr_results = {"p1": pr1, "p2": pr2}

    # Compute per-position PnL using public API
    p1 = compute_position_pnl(
        position_id="p1",
        symbol="A",
        prev_pr=prev1,
        curr_pr=pr1,
        prev_snapshot=None,
        curr_snapshot=None,
        quantity=1.0,
        base_currency="USD",
        fx_converter=fx,
        mode="step",
    )
    p2 = compute_position_pnl(
        position_id="p2",
        symbol="B",
        prev_pr=prev2,
        curr_pr=pr2,
        prev_snapshot=None,
        curr_snapshot=None,
        quantity=1.0,
        base_currency="USD",
        fx_converter=fx,
        mode="step",
    )

    # Sum components
    sum_pv = math.fsum([p1.pv, p2.pv])
    sum_pnl = math.fsum([p1.pnl, p2.pnl])

    # Portfolio-level API
    portfolio = compute_portfolio_pnl(
        positions=[pos1, pos2],
        prev_results=prev_results,
        curr_results=curr_results,
        prev_snapshot=None,
        curr_snapshot=None,
        base_currency="USD",
        fx_converter=fx,
        mode="step",
    )

    assert _close(sum_pv, portfolio.total_pv, MetricClass.PRICE), (
        f"PV mismatch: sum={sum_pv} portfolio={portfolio.total_pv}"
    )
    assert _close(sum_pnl, portfolio.total_pnl, MetricClass.PNL), (
        f"PnL mismatch: sum={sum_pnl} portfolio={portfolio.total_pnl}"
    )


def test_permutation_invariance_of_breakdown():
    fx = dummy_fx()
    pr1 = make_price(100.0, "USD", {"delta": 1.0})
    prev1 = make_price(90.0, "USD", {"delta": 1.0})
    pr2 = make_price(200.0, "USD", {"delta": 0.0})
    prev2 = make_price(190.0, "USD", {"delta": 0.0})

    p1 = compute_position_pnl(
        position_id="p1",
        symbol="A",
        prev_pr=prev1,
        curr_pr=pr1,
        prev_snapshot=None,
        curr_snapshot=None,
        quantity=1.0,
        base_currency="USD",
        fx_converter=fx,
        mode="step",
    )
    p2 = compute_position_pnl(
        position_id="p2",
        symbol="B",
        prev_pr=prev2,
        curr_pr=pr2,
        prev_snapshot=None,
        curr_snapshot=None,
        quantity=1.0,
        base_currency="USD",
        fx_converter=fx,
        mode="step",
    )

    # Two orders
    order1 = [p1, p2]
    order2 = [p2, p1]

    bd1 = compute_portfolio_pnl_breakdown(positions_inputs=order1, base_currency="USD")
    bd2 = compute_portfolio_pnl_breakdown(positions_inputs=order2, base_currency="USD")

    # totals must match within PNL tolerances
    assert _close(bd1.total_pnl, bd2.total_pnl, MetricClass.PNL)

    # items are deterministically sorted inside the breakdown; equality expected
    assert bd1.items == bd2.items
