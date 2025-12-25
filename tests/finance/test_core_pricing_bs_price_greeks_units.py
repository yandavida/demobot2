from core.pricing.bs import bs_greeks
from core.pricing import bs_price_greeks

def test_core_pricing_bs_price_greeks_units():
    # Example params: ATM call
    params = dict(spot=100, strike=100, t=1.0, rate=0.01, div=0.0, vol=0.2, cp="C")
    g = bs_greeks(**params)
    # bs_price_greeks: S, K, r, q, sigma, T, cp
    ret = bs_price_greeks(
        params["spot"],
        params["strike"],
        params["rate"],
        params["div"],
        params["vol"],
        params["t"],
        params["cp"],
    )
    # vega: per 1% vol
    assert abs(ret.vega - g['vega'] / 100.0) < 1e-10
    # theta: per day
    assert abs(ret.theta - g['theta'] / 365.0) < 1e-10
