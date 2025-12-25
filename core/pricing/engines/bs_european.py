import math
from core.pricing.inputs import PricingInput

def price_european_bs(inp: PricingInput) -> float:
    inp.validate()
    S, K, T, r, q, sigma = inp.spot, inp.strike, inp.t_expiry_years, inp.rate, inp.div_yield, inp.vol
    if T == 0:
        return max((S - K) if inp.is_call else (K - S), 0.0)
    if sigma == 0:
        df = math.exp(-r * T)
        fwd = S * math.exp((r - q) * T)
        return df * max((fwd - K) if inp.is_call else (K - fwd), 0.0)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    from math import erf, sqrt
    def norm_cdf(x):
        return 0.5 * (1 + erf(x / sqrt(2)))
    if inp.is_call:
        price = S * math.exp(-q * T) * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
    else:
        price = K * math.exp(-r * T) * norm_cdf(-d2) - S * math.exp(-q * T) * norm_cdf(-d1)
    return price
