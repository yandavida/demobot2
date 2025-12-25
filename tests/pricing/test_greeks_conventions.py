from core.pricing.inputs import PricingInput
from core.pricing.engines.bs_european import price_european_bs
from core.pricing.greeks import greeks_bump

def test_greeks_conventions():
    inp = PricingInput(spot=100.0, strike=100.0, t_expiry_years=1.0, rate=0.05, div_yield=0.0, vol=0.2, is_call=True)
    greeks = greeks_bump(price_european_bs, inp)
    from core.pricing.units import to_canonical_greeks
    canon = to_canonical_greeks({
        'delta': greeks.delta,
        'gamma': greeks.gamma,
        'vega': greeks.vega,
        'theta': greeks.theta,
        'rho': greeks.rho,
    })
    class G:
        pass
    greeks = G()
    greeks.delta = canon['delta']
    greeks.gamma = canon['gamma']
    greeks.vega = canon['vega']
    greeks.theta = canon['theta']
    greeks.rho = canon['rho']
    # Vega: price(vol+0.01)-price(vol)
    inp_vega = PricingInput(spot=100.0, strike=100.0, t_expiry_years=1.0, rate=0.05, div_yield=0.0, vol=0.21, is_call=True)
    vega_fd = (price_european_bs(inp_vega) - price_european_bs(inp)) / 0.01 / 100.0
    assert abs(greeks.vega - vega_fd) < 1e-3
    # Theta: per day
    inp_theta = PricingInput(spot=100.0, strike=100.0, t_expiry_years=1.0 - 1/365, rate=0.05, div_yield=0.0, vol=0.2, is_call=True)
    theta_fd = (price_european_bs(inp_theta) - price_european_bs(inp)) / - (1/365) / 365.0
    assert abs(greeks.theta - theta_fd) < 1e-3
    # Bump-consistency: vega ≈ price(vol+0.01)-price(vol), theta ≈ price(T-1/365)-price(T)
    from pytest import approx
    assert greeks.vega == approx((price_european_bs(inp_vega) - price_european_bs(inp)) / 0.01 / 100.0, rel=1e-6, abs=1e-8)
    assert greeks.theta == approx((price_european_bs(inp_theta) - price_european_bs(inp)) / -(1/365) / 365.0, rel=1e-6, abs=1e-8)
