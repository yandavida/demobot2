from core.pricing.bs import bs_greeks
from core.pricing.units import to_canonical_greeks

def test_bs_greeks_to_canonical_units():
    # Example params: ATM call
    g = bs_greeks(spot=100, strike=100, t=1.0, rate=0.01, div=0.0, vol=0.2, cp="C")
    canon = to_canonical_greeks(g)
    # vega: per 1% vol
    assert abs(canon['vega'] - g['vega'] / 100.0) < 1e-10
    # theta: per day
    assert abs(canon['theta'] - g['theta'] / 365.0) < 1e-10
