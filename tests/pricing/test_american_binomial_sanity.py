from core.pricing.inputs import PricingInput
from core.pricing.engines.bs_european import price_european_bs
from core.pricing.engines.binomial_american import price_american_binomial_crr

def test_american_call_vs_european():
    inp = PricingInput(spot=100.0, strike=100.0, t_expiry_years=1.0, rate=0.05, div_yield=0.0, vol=0.2, is_call=True)
    euro = price_european_bs(inp)
    amer = price_american_binomial_crr(inp, steps=500)
    assert abs(euro - amer) < 0.02  # Should be very close

def test_american_put_ge_european():
    inp = PricingInput(spot=100.0, strike=100.0, t_expiry_years=1.0, rate=0.05, div_yield=0.0, vol=0.2, is_call=False)
    euro = price_european_bs(inp)
    amer = price_american_binomial_crr(inp, steps=500)
    assert amer >= euro

def test_monotonicity():
    inp = PricingInput(spot=100.0, strike=100.0, t_expiry_years=1.0, rate=0.05, div_yield=0.0, vol=0.2, is_call=True)
    up = PricingInput(spot=110.0, strike=100.0, t_expiry_years=1.0, rate=0.05, div_yield=0.0, vol=0.2, is_call=True)
    assert price_american_binomial_crr(up, steps=200) > price_american_binomial_crr(inp, steps=200)
