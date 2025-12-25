import math
from core.pricing.inputs import PricingInput

def price_american_binomial_crr(inp: PricingInput, steps: int = 200) -> float:
    inp.validate()
    S, K, T, r, q, sigma = inp.spot, inp.strike, inp.t_expiry_years, inp.rate, inp.div_yield, inp.vol
    if T == 0:
        return max((S - K) if inp.is_call else (K - S), 0.0)
    if sigma == 0 or steps < 1:
        df = math.exp(-r * T)
        fwd = S * math.exp((r - q) * T)
        return df * max((fwd - K) if inp.is_call else (K - fwd), 0.0)
    dt = T / steps
    u = math.exp(sigma * math.sqrt(dt))
    d = 1 / u
    disc = math.exp(-r * dt)
    p = (math.exp((r - q) * dt) - d) / (u - d)
    # build tree
    values = [0.0] * (steps + 1)
    for j in range(steps + 1):
        S_T = S * (u ** j) * (d ** (steps - j))
        values[j] = max((S_T - K) if inp.is_call else (K - S_T), 0.0)
    for i in range(steps - 1, -1, -1):
        for j in range(i + 1):
            S_t = S * (u ** j) * (d ** (i - j))
            hold = disc * (p * values[j + 1] + (1 - p) * values[j])
            exercise = max((S_t - K) if inp.is_call else (K - S_t), 0.0)
            values[j] = max(hold, exercise)
    return values[0]
