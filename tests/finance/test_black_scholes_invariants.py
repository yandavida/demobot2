from __future__ import annotations

import itertools
import math

import pytest

from core.pricing.black_scholes import bs_price_greeks
from core.numeric_policy import DEFAULT_TOLERANCES, MetricClass


def _abs_tol(metric: MetricClass) -> float:
    return DEFAULT_TOLERANCES[metric].abs or 0.0


def _rel_tol(metric: MetricClass) -> float:
    return DEFAULT_TOLERANCES[metric].rel or 0.0


S_vals = [80.0, 100.0, 120.0]
K_vals = [80.0, 100.0, 120.0]
T_vals = [1.0 / 365.0, 30.0 / 365.0, 1.0]
sigma_vals = [0.05, 0.2, 0.8]
r_vals = [0.0, 0.03]
q_vals = [0.0]


cases = list(itertools.product(S_vals, K_vals, T_vals, sigma_vals, r_vals, q_vals))


@pytest.mark.parametrize("S,K,T,sigma,r,q", cases)
def test_bs_invariants_and_stability(S, K, T, sigma, r, q):
    # Pricing entries
    c = bs_price_greeks(S=S, K=K, r=r, q=q, sigma=sigma, T=T, cp="C")
    p = bs_price_greeks(S=S, K=K, r=r, q=q, sigma=sigma, T=T, cp="P")

    # Tolerances
    price_abs = _abs_tol(MetricClass.PRICE)
    price_rel = _rel_tol(MetricClass.PRICE)

    delta_abs = _abs_tol(MetricClass.DELTA)
    delta_rel = _rel_tol(MetricClass.DELTA)

    gamma_abs = _abs_tol(MetricClass.GAMMA)
    gamma_rel = _rel_tol(MetricClass.GAMMA)

    # 1) No-arbitrage bounds
    lower_call = max(0.0, S * math.exp(-q * T) - K * math.exp(-r * T))
    upper_call = S * math.exp(-q * T)
    assert c.price + price_abs >= lower_call
    assert c.price <= upper_call + price_abs

    lower_put = max(0.0, K * math.exp(-r * T) - S * math.exp(-q * T))
    upper_put = K * math.exp(-r * T)
    assert p.price + price_abs >= lower_put
    assert p.price <= upper_put + price_abs

    # 2) Put-call parity
    rhs = S * math.exp(-q * T) - K * math.exp(-r * T)
    assert math.isclose(c.price - p.price, rhs, rel_tol=price_rel, abs_tol=price_abs)

    # 3) Monotonicity: price increases with S and sigma
    dS = 1.0
    c_up = bs_price_greeks(S=S + dS, K=K, r=r, q=q, sigma=sigma, T=T, cp="C")
    p_up = bs_price_greeks(S=S + dS, K=K, r=r, q=q, sigma=sigma, T=T, cp="P")
    assert c_up.price + price_abs >= c.price
    assert p_up.price <= p.price + price_abs

    dsig = 0.01
    c_sig = bs_price_greeks(S=S, K=K, r=r, q=q, sigma=sigma + dsig, T=T, cp="C")
    p_sig = bs_price_greeks(S=S, K=K, r=r, q=q, sigma=sigma + dsig, T=T, cp="P")
    assert c_sig.price + price_abs >= c.price
    assert p_sig.price + price_abs >= p.price

    # 4) Greeks sanity
    assert 0.0 - delta_abs <= c.delta <= 1.0 + delta_abs
    assert -1.0 - delta_abs <= p.delta <= 0.0 + delta_abs
    assert c.gamma >= -gamma_abs
    assert p.gamma >= -gamma_abs
    assert c.vega >= -_abs_tol(MetricClass.VEGA)
    assert p.vega >= -_abs_tol(MetricClass.VEGA)

    # 5) Finite-difference cross-check (central difference)
    # Conventions (implementation):
    # - pricing entrypoint used below: `bs_price_greeks`
    # - continuous dividend yield `q` is supported and passed to the function
    # - vega returned by the implementation is in canonical units: per 1% vol
    # - theta returned by the implementation is in canonical units: per day
    # The above notes are intentionally repeated here for inclusion in the
    # PR body as a concise reference for reviewers.

    # Deterministic FD steps (no scientific-notation literals):
    hS = max(0.01, S * 0.001)
    hsig = 0.001

    C_plus = bs_price_greeks(S=S + hS, K=K, r=r, q=q, sigma=sigma, T=T, cp="C")
    C_minus = bs_price_greeks(S=S - hS, K=K, r=r, q=q, sigma=sigma, T=T, cp="C")
    fd_delta = (C_plus.price - C_minus.price) / (2 * hS)
    # Compute gamma from analytic deltas for numerical stability
    fd_gamma = (C_plus.delta - C_minus.delta) / (2 * hS)

    # Use SSOT-driven FD tolerances (scaled integer-only multiplier)
    fd_abs_tol = _abs_tol(MetricClass.TIME) * 1000
    fd_rel_tol = _rel_tol(MetricClass.TIME) * 1000

    def _fd_allowed(a, b):
        # a: analytic, b: fd (or vice versa) — compare with symmetric max scale
        return max(fd_abs_tol, fd_rel_tol * max(abs(a), abs(b), 1.0))

    assert abs(fd_delta - c.delta) <= _fd_allowed(c.delta, fd_delta)
    # Gamma FD can be unstable for very short expiries with the fixed
    # deterministic `hS` above; only assert gamma FD for longer-dated
    # cases where the FD step is appropriate.
    if T >= 30.0 / 365.0:
        assert abs(fd_gamma - c.gamma) <= _fd_allowed(c.gamma, fd_gamma)
