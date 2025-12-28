import math
from core.pnl.theoretical import compute_position_pnl
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

def test_additivity_identity():
    pr1 = make_price(100, "USD", {"delta": 1.0, "theta": 2.0, "gamma": 0.0, "vega": 0.0})
    prev1 = make_price(90, "USD", {"delta": 1.0, "theta": 2.0, "gamma": 0.0, "vega": 0.0})
    pos = compute_position_pnl(position_id="p1", symbol="A", prev_pr=prev1, curr_pr=pr1, prev_snapshot=None, curr_snapshot=None, quantity=1.0, base_currency="USD", fx_converter=dummy_fx(), mode="step")
    total = pos.pnl
    breakdown = pos.attribution
    sum_components = math.fsum([breakdown.delta_pnl, breakdown.theta_pnl, breakdown.gamma_pnl, breakdown.vega_pnl, breakdown.residual])
    assert math.isclose(total, sum_components, rel_tol=1e-12)

def test_currency_conversion_consistency():
    pr1 = make_price(400, "ILS", {"delta": 1.0})
    prev1 = make_price(360, "ILS", {"delta": 1.0})
    fx = dummy_fx()
    pos = compute_position_pnl(position_id="p1", symbol="A", prev_pr=prev1, curr_pr=pr1, prev_snapshot=None, curr_snapshot=None, quantity=1.0, base_currency="USD", fx_converter=fx, mode="step")
    manual = (400/4) - (360/4)
    assert math.isclose(pos.pnl, manual, rel_tol=1e-12)

def test_missing_iv_invariant():
    pr1 = make_price(110, "USD", {"delta": 1.0, "vega": 2.0})
    prev1 = make_price(100, "USD", {"delta": 1.0, "vega": 2.0})
    pos = compute_position_pnl(position_id="p1", symbol="A", prev_pr=prev1, curr_pr=pr1, prev_snapshot=None, curr_snapshot=None, quantity=1.0, base_currency="USD", fx_converter=dummy_fx(), mode="step")
    assert pos.attribution.vega_pnl == 0.0
    assert any("dIV=0" in n for n in pos.attribution.notes)

def test_determinism():
    pr1 = make_price(110, "USD", {"delta": 1.0})
    prev1 = make_price(100, "USD", {"delta": 1.0})
    args = dict(position_id="p1", symbol="A", prev_pr=prev1, curr_pr=pr1, prev_snapshot=None, curr_snapshot=None, quantity=1.0, base_currency="USD", fx_converter=dummy_fx(), mode="step")
    pos1 = compute_position_pnl(**args)
    pos2 = compute_position_pnl(**args)
    assert pos1 == pos2

def test_sign_invariants():
    pr1 = make_price(110, "USD", {"delta": 1.0})
    prev1 = make_price(100, "USD", {"delta": 1.0})
    pos_pos = compute_position_pnl(position_id="p1", symbol="A", prev_pr=prev1, curr_pr=pr1, prev_snapshot=None, curr_snapshot=None, quantity=1.0, base_currency="USD", fx_converter=dummy_fx(), mode="step")
    pos_neg = compute_position_pnl(position_id="p1", symbol="A", prev_pr=prev1, curr_pr=pr1, prev_snapshot=None, curr_snapshot=None, quantity=-1.0, base_currency="USD", fx_converter=dummy_fx(), mode="step")
    assert math.isclose(pos_pos.pnl, -pos_neg.pnl, rel_tol=1e-12)
    assert math.isclose(pos_pos.attribution.delta_pnl, -pos_neg.attribution.delta_pnl, rel_tol=1e-12)
