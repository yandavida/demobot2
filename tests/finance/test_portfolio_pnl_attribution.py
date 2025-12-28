import math
from core.pnl.theoretical import compute_position_pnl
from core.contracts.money import Currency

class DummyFxConverter:
    def convert(self, amount: float, from_ccy: Currency, to_ccy: Currency, *, strict: bool = True) -> float:
        if from_ccy == to_ccy:
            return float(amount)
        if from_ccy == "USD" and to_ccy == "ILS":
            return float(amount) * 4
        if from_ccy == "ILS" and to_ccy == "USD":
            return float(amount) / 4
        raise ValueError("Unsupported currency conversion")

def make_positions():
    pr1 = type("PriceResult", (), {"pv": 100.0, "currency": "USD", "breakdown": {"delta": 1.0, "theta": 2.0}})()
    pr2 = type("PriceResult", (), {"pv": 200.0, "currency": "USD", "breakdown": {"delta": 2.0, "theta": 3.0}})()
    pr3 = type("PriceResult", (), {"pv": 400.0, "currency": "ILS", "breakdown": {"delta": 4.0, "theta": 5.0}})()
    prev_pr1 = type("PriceResult", (), {"pv": 90.0, "currency": "USD", "breakdown": {"delta": 1.0, "theta": 2.0}})()
    prev_pr2 = type("PriceResult", (), {"pv": 180.0, "currency": "USD", "breakdown": {"delta": 2.0, "theta": 3.0}})()
    prev_pr3 = type("PriceResult", (), {"pv": 360.0, "currency": "ILS", "breakdown": {"delta": 4.0, "theta": 5.0}})()
    fx = DummyFxConverter()
    pos1 = compute_position_pnl(position_id="p1", symbol="A", prev_pr=prev_pr1, curr_pr=pr1, prev_snapshot=None, curr_snapshot=None, quantity=1.0, base_currency="USD", fx_converter=fx, mode="step")
    pos2 = compute_position_pnl(position_id="p2", symbol="B", prev_pr=prev_pr2, curr_pr=pr2, prev_snapshot=None, curr_snapshot=None, quantity=1.0, base_currency="USD", fx_converter=fx, mode="step")
    pos3 = compute_position_pnl(position_id="p3", symbol="C", prev_pr=prev_pr3, curr_pr=pr3, prev_snapshot=None, curr_snapshot=None, quantity=1.0, base_currency="USD", fx_converter=fx, mode="step")
    return [pos1, pos2, pos3]

def test_additivity():
    from core.pnl.portfolio_breakdown import compute_portfolio_pnl_breakdown
    positions = make_positions()
    portfolio = compute_portfolio_pnl_breakdown(positions_inputs=positions, base_currency="USD")
    # Additivity
    assert math.isclose(portfolio.total_pnl, sum(p.pnl for p in positions), rel_tol=1e-12)
    assert math.isclose(portfolio.delta_pnl, sum(p.attribution.delta_pnl for p in positions), rel_tol=1e-12)
    assert math.isclose(portfolio.theta_pnl, sum(p.attribution.theta_pnl for p in positions), rel_tol=1e-12)
    assert math.isclose(portfolio.residual, sum(p.attribution.residual for p in positions), rel_tol=1e-12)
    # Closure
    total_breakdown = portfolio.delta_pnl + portfolio.theta_pnl + portfolio.gamma_pnl + portfolio.vega_pnl + portfolio.residual
    assert math.isclose(portfolio.total_pnl, total_breakdown, rel_tol=1e-12)

def test_permutation_invariance():
    from core.pnl.portfolio_breakdown import compute_portfolio_pnl_breakdown
    positions = make_positions()
    perm1 = positions
    perm2 = [positions[2], positions[0], positions[1]]
    p1 = compute_portfolio_pnl_breakdown(positions_inputs=perm1, base_currency="USD")
    p2 = compute_portfolio_pnl_breakdown(positions_inputs=perm2, base_currency="USD")
    assert p1.total_pnl == p2.total_pnl
    assert p1.delta_pnl == p2.delta_pnl
    assert p1.theta_pnl == p2.theta_pnl
    assert p1.gamma_pnl == p2.gamma_pnl
    assert p1.vega_pnl == p2.vega_pnl
    assert p1.residual == p2.residual
    # Items sorted
    ids1 = [(x.symbol, x.position_id) for x in p1.items]
    ids2 = [(x.symbol, x.position_id) for x in p2.items]
    assert ids1 == ids2

def test_mixed_currencies():
    from core.pnl.portfolio_breakdown import compute_portfolio_pnl_breakdown
    fx = DummyFxConverter()
    pr_usd = type("PriceResult", (), {"pv": 100.0, "currency": "USD", "breakdown": {"delta": 1.0}})()
    pr_ils = type("PriceResult", (), {"pv": 400.0, "currency": "ILS", "breakdown": {"delta": 1.0}})()
    prev_usd = type("PriceResult", (), {"pv": 90.0, "currency": "USD", "breakdown": {"delta": 1.0}})()
    prev_ils = type("PriceResult", (), {"pv": 360.0, "currency": "ILS", "breakdown": {"delta": 1.0}})()
    pos_usd = compute_position_pnl(position_id="usd", symbol="USD", prev_pr=prev_usd, curr_pr=pr_usd, prev_snapshot=None, curr_snapshot=None, quantity=1.0, base_currency="USD", fx_converter=fx, mode="step")
    pos_ils = compute_position_pnl(position_id="ils", symbol="ILS", prev_pr=prev_ils, curr_pr=pr_ils, prev_snapshot=None, curr_snapshot=None, quantity=1.0, base_currency="USD", fx_converter=fx, mode="step")
    portfolio = compute_portfolio_pnl_breakdown(positions_inputs=[pos_usd, pos_ils], base_currency="USD")
    assert math.isclose(portfolio.total_pnl, pos_usd.pnl + pos_ils.pnl, rel_tol=1e-12)

def test_missing_iv_propagation():
    from core.pnl.portfolio_breakdown import compute_portfolio_pnl_breakdown
    fx = DummyFxConverter()
    pr1 = type("PriceResult", (), {"pv": 100.0, "currency": "USD", "breakdown": {"delta": 1.0, "vega": 2.0}})()
    prev1 = type("PriceResult", (), {"pv": 90.0, "currency": "USD", "breakdown": {"delta": 1.0, "vega": 2.0}})()
    pos1 = compute_position_pnl(position_id="p1", symbol="A", prev_pr=prev1, curr_pr=pr1, prev_snapshot=None, curr_snapshot=None, quantity=1.0, base_currency="USD", fx_converter=fx, mode="step")
    portfolio = compute_portfolio_pnl_breakdown(positions_inputs=[pos1], base_currency="USD")
    # notes propagate
    notes = [n for x in portfolio.items for n in x.attribution.notes]
    assert any("dIV=0" in n for n in notes)
    # notes_summary (if present)
    if hasattr(portfolio, "notes_summary"):
        assert portfolio.notes_summary.get("dIV=0", 0) >= 1
