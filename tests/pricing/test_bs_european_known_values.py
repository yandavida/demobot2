import math
from core.pricing.inputs import PricingInput
from core.pricing.engines.bs_european import price_european_bs

def test_bs_european_known_values():
    # Golden values (from scipy.stats or known calculators)
    inp_call = PricingInput(spot=100.0, strike=100.0, t_expiry_years=1.0, rate=0.05, div_yield=0.0, vol=0.2, is_call=True)
    inp_put = PricingInput(spot=100.0, strike=100.0, t_expiry_years=1.0, rate=0.05, div_yield=0.0, vol=0.2, is_call=False)
    call_val = price_european_bs(inp_call)
    put_val = price_european_bs(inp_put)
    # Reference: call ≈ 10.4506, put ≈ 5.5735
    assert math.isclose(call_val, 10.4506, rel_tol=1e-4)
    assert math.isclose(put_val, 5.5735, rel_tol=1e-4)
    # Monotonicity
    inp_call2 = PricingInput(spot=110.0, strike=100.0, t_expiry_years=1.0, rate=0.05, div_yield=0.0, vol=0.2, is_call=True)
    assert price_european_bs(inp_call2) > call_val
    inp_put2 = PricingInput(spot=90.0, strike=100.0, t_expiry_years=1.0, rate=0.05, div_yield=0.0, vol=0.2, is_call=False)
    assert price_european_bs(inp_put2) > put_val
    # Volatility up
    inp_call3 = PricingInput(spot=100.0, strike=100.0, t_expiry_years=1.0, rate=0.05, div_yield=0.0, vol=0.3, is_call=True)
    assert price_european_bs(inp_call3) > call_val
