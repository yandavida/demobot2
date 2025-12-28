import math
from core.pnl.theoretical import compute_position_pnl
from core.pnl.portfolio_breakdown import compute_portfolio_pnl_breakdown
from core.contracts.money import Currency

def dummy_fx():
    class DummyFxConverter:
        def convert(self, amount: float, from_ccy: Currency, to_ccy: Currency, *, strict: bool = True) -> float:
            if from_ccy == to_ccy:
                return float(amount)
            if from_ccy == "USD" and to_ccy == "ILS":
                return float(amount) * 4
            if from_ccy == "ILS" and to_ccy == "USD":
                return float(amount) / 4
            raise ValueError("Unsupported currency conversion")
    return DummyFxConverter()

def make_price(pv, ccy, breakdown):
    return type("PriceResult", (), {"pv": pv, "currency": ccy, "breakdown": breakdown})()

def test_portfolio_additivity():
    pr1 = make_price(100, "USD", {"delta": 1.0, "theta": 2.0, "gamma": 0.0, "vega": 0.0})
    prev1 = make_price(90, "USD", {"delta": 1.0, "theta": 2.0, "gamma": 0.0, "vega": 0.0})
    pr2 = make_price(400, "ILS", {"delta": 2.0, "theta": 1.0, "gamma": 0.0, "vega": 0.0})
    prev2 = make_price(360, "ILS", {"delta": 2.0, "theta": 1.0, "gamma": 0.0, "vega": 0.0})
    fx = dummy_fx()
    pos1 = compute_position_pnl(position_id="p1", symbol="A", prev_pr=prev1, curr_pr=pr1, prev_snapshot=None, curr_snapshot=None, quantity=1.0, base_currency="USD", fx_converter=fx, mode="step")
    pos2 = compute_position_pnl(position_id="p2", symbol="B", prev_pr=prev2, curr_pr=pr2, prev_snapshot=None, curr_snapshot=None, quantity=1.0, base_currency="USD", fx_converter=fx, mode="step")
    portfolio = compute_portfolio_pnl_breakdown(positions_inputs=[pos1, pos2], base_currency="USD")
    assert math.isclose(portfolio.total_pnl, pos1.pnl + pos2.pnl, rel_tol=1e-12)
    assert math.isclose(portfolio.delta_pnl, pos1.attribution.delta_pnl + pos2.attribution.delta_pnl, rel_tol=1e-12)
    assert math.isclose(portfolio.theta_pnl, pos1.attribution.theta_pnl + pos2.attribution.theta_pnl, rel_tol=1e-12)
    assert math.isclose(portfolio.residual, pos1.attribution.residual + pos2.attribution.residual, rel_tol=1e-12)
    total_breakdown = math.fsum([portfolio.delta_pnl, portfolio.theta_pnl, portfolio.gamma_pnl, portfolio.vega_pnl, portfolio.residual])
    assert math.isclose(portfolio.total_pnl, total_breakdown, rel_tol=1e-12)

def test_portfolio_permutation_invariance():
    pr1 = make_price(100, "USD", {"delta": 1.0})
    prev1 = make_price(90, "USD", {"delta": 1.0})
    pr2 = make_price(400, "ILS", {"delta": 2.0})
    prev2 = make_price(360, "ILS", {"delta": 2.0})
    fx = dummy_fx()
    pos1 = compute_position_pnl(position_id="p1", symbol="A", prev_pr=prev1, curr_pr=pr1, prev_snapshot=None, curr_snapshot=None, quantity=1.0, base_currency="USD", fx_converter=fx, mode="step")
    pos2 = compute_position_pnl(position_id="p2", symbol="B", prev_pr=prev2, curr_pr=pr2, prev_snapshot=None, curr_snapshot=None, quantity=1.0, base_currency="USD", fx_converter=fx, mode="step")
    perm1 = [pos1, pos2]
    perm2 = [pos2, pos1]
    p1 = compute_portfolio_pnl_breakdown(positions_inputs=perm1, base_currency="USD")
    p2 = compute_portfolio_pnl_breakdown(positions_inputs=perm2, base_currency="USD")
    assert p1.total_pnl == p2.total_pnl
    assert p1.delta_pnl == p2.delta_pnl
    assert p1.theta_pnl == p2.theta_pnl
    assert p1.gamma_pnl == p2.gamma_pnl
    assert p1.vega_pnl == p2.vega_pnl
    assert p1.residual == p2.residual
    ids1 = [(x.symbol, x.position_id) for x in p1.items]
    ids2 = [(x.symbol, x.position_id) for x in p2.items]
    assert ids1 == ids2

def test_portfolio_mixed_currencies():
    pr1 = make_price(100, "USD", {"delta": 1.0})
    prev1 = make_price(90, "USD", {"delta": 1.0})
    pr2 = make_price(400, "ILS", {"delta": 1.0})
    prev2 = make_price(360, "ILS", {"delta": 1.0})
    fx = dummy_fx()
    pos1 = compute_position_pnl(position_id="usd", symbol="USD", prev_pr=prev1, curr_pr=pr1, prev_snapshot=None, curr_snapshot=None, quantity=1.0, base_currency="USD", fx_converter=fx, mode="step")
    pos2 = compute_position_pnl(position_id="ils", symbol="ILS", prev_pr=prev2, curr_pr=pr2, prev_snapshot=None, curr_snapshot=None, quantity=1.0, base_currency="USD", fx_converter=fx, mode="step")
    portfolio = compute_portfolio_pnl_breakdown(positions_inputs=[pos1, pos2], base_currency="USD")
    assert math.isclose(portfolio.total_pnl, pos1.pnl + pos2.pnl, rel_tol=1e-12)

def test_portfolio_notes_traceability():
    pr1 = make_price(110, "USD", {"delta": 1.0, "vega": 2.0})
    prev1 = make_price(100, "USD", {"delta": 1.0, "vega": 2.0})
    fx = dummy_fx()
    pos1 = compute_position_pnl(position_id="p1", symbol="A", prev_pr=prev1, curr_pr=pr1, prev_snapshot=None, curr_snapshot=None, quantity=1.0, base_currency="USD", fx_converter=fx, mode="step")
    portfolio = compute_portfolio_pnl_breakdown(positions_inputs=[pos1], base_currency="USD")
    notes = [n for x in portfolio.items for n in x.attribution.notes]
    assert any("dIV=0" in n for n in notes)
    if hasattr(portfolio, "notes_summary"):
        assert portfolio.notes_summary.get("dIV=0", 0) >= 1
