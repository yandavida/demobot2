from dataclasses import dataclass
from core.pricing.inputs import PricingInput
from dataclasses import replace

@dataclass(frozen=True)
class Greeks:
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float

def greeks_bump(price_fn, inp: PricingInput, *, spot_bump=0.01, vol_bump=0.01, rate_bump=0.01) -> Greeks:
    inp.validate()
    # Delta & Gamma (central diff)
    inp_up = replace(inp, spot=inp.spot + spot_bump)
    inp_dn = replace(inp, spot=inp.spot - spot_bump)
    p_up = price_fn(inp_up)
    p_dn = price_fn(inp_dn)
    p0 = price_fn(inp)
    delta = (p_up - p_dn) / (2 * spot_bump)
    gamma = (p_up - 2 * p0 + p_dn) / (spot_bump ** 2)
    # Vega (raw)
    inp_vega = replace(inp, vol=inp.vol + vol_bump)
    vega = (price_fn(inp_vega) - p0) / vol_bump
    # Rho
    inp_rho = replace(inp, rate=inp.rate + rate_bump)
    rho = (price_fn(inp_rho) - p0) / rate_bump
    # Theta (raw)
    dt = 1 / 365
    t_minus = max(inp.t_expiry_years - dt, 1e-8)
    inp_theta = replace(inp, t_expiry_years=t_minus)
    theta = (price_fn(inp_theta) - p0) / -dt
    # Return raw greeks (no normalization)
    return Greeks(
        delta=delta,
        gamma=gamma,
        vega=vega,
        theta=theta,
        rho=rho,
    )
