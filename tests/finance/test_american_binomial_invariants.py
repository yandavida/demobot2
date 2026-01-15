from __future__ import annotations

import math

import pytest

from core.pricing.engines.binomial_american import price_american_binomial_crr
from core.pricing.bs import bs_price
from core.pricing.inputs import PricingInput
from core.numeric_policy import DEFAULT_TOLERANCES, MetricClass


# Helper: SSOT tolerances for prices
PRICE_TOL = DEFAULT_TOLERANCES[MetricClass.PRICE]


def _assert_close(a: float, b: float) -> None:
    abs_tol = PRICE_TOL.abs or 0.0
    rel_tol = PRICE_TOL.rel or 0.0
    limit = max(abs_tol, rel_tol * max(abs(a), abs(b), 1.0))
    assert abs(a - b) <= limit, f"Values differ more than tolerance: |{a} - {b}| > {limit}"


def _leq_with_tol(a: float, b: float) -> None:
    # assert a <= b + tol
    abs_tol = PRICE_TOL.abs or 0.0
    rel_tol = PRICE_TOL.rel or 0.0
    limit = max(abs_tol, rel_tol * max(abs(a), abs(b), 1.0))
    assert a <= b + limit, f"Expected {a} <= {b} + tol ({limit})"


@pytest.mark.parametrize("S,K,T,sigma,r,q,is_call", [
    (80.0, 100.0, 30.0 / 365.0, 0.10, 0.0, 0.0, True),
    (100.0, 100.0, 1.0, 0.25, 0.03, 0.02, True),
    (120.0, 100.0, 1.0, 0.25, 0.03, 0.02, False),
])
def test_no_arbitrage_bounds(S, K, T, sigma, r, q, is_call):
    # basic bounds: non-negative and bounded by spot/strike (discounted where appropriate)
    inp = PricingInput(float(S), float(K), float(T), float(r), float(q), float(sigma), bool(is_call))
    a_price = price_american_binomial_crr(inp, steps=500)

    assert a_price >= 0.0
    if is_call:
        assert a_price <= S + 1e-12
    else:
        # put can't exceed strike (per-unit)
        assert a_price <= K + 1e-12

    # lower no-arb bound using forward PV convention from bs.py
    df_r = math.exp(-r * T)
    df_q = math.exp(-q * T)
    call_lb = max(0.0, S * df_q - K * df_r)
    put_lb = max(0.0, K * df_r - S * df_q)
    if is_call:
        assert a_price + 0.0 >= call_lb - 1e-12
    else:
        assert a_price + 0.0 >= put_lb - 1e-12


@pytest.mark.parametrize("S_low,S_high", [(80.0, 100.0), (100.0, 120.0)])
def test_monotonicity_spot(S_low, S_high):
    # for calls: price increases with spot; for puts: price decreases with spot
    K = 100.0
    T = 0.5
    sigma = 0.2
    r = 0.01
    q = 0.0

    inp_low_call = PricingInput(float(S_low), float(K), float(T), float(r), float(q), float(sigma), True)
    inp_high_call = PricingInput(float(S_high), float(K), float(T), float(r), float(q), float(sigma), True)
    p_low = price_american_binomial_crr(inp_low_call, steps=500)
    p_high = price_american_binomial_crr(inp_high_call, steps=500)
    assert p_high >= p_low - (PRICE_TOL.abs or 0.0)

    inp_low_put = PricingInput(float(S_low), float(K), float(T), float(r), float(q), float(sigma), False)
    inp_high_put = PricingInput(float(S_high), float(K), float(T), float(r), float(q), float(sigma), False)
    pu_low = price_american_binomial_crr(inp_low_put, steps=500)
    pu_high = price_american_binomial_crr(inp_high_put, steps=500)
    assert pu_low >= pu_high - (PRICE_TOL.abs or 0.0)


@pytest.mark.parametrize("vol_low,vol_high", [(0.10, 0.25)])
def test_monotonicity_vol(vol_low, vol_high):
    S = 100.0
    K = 100.0
    T = 1.0
    r = 0.01
    q = 0.0

    inp_low = PricingInput(float(S), float(K), float(T), float(r), float(q), float(vol_low), True)
    inp_high = PricingInput(float(S), float(K), float(T), float(r), float(q), float(vol_high), True)
    p_low = price_american_binomial_crr(inp_low, steps=500)
    p_high = price_american_binomial_crr(inp_high, steps=500)
    assert p_high >= p_low - (PRICE_TOL.abs or 0.0)


@pytest.mark.parametrize("S,K,T,sigma,r,option_is_call", [
    (100.0, 100.0, 0.5, 0.2, 0.01, True),
    (90.0, 100.0, 1.0, 0.25, 0.02, False),
])
def test_american_ge_european(S, K, T, sigma, r, option_is_call):
    # American >= European (price-only checks)
    q = 0.02 if not option_is_call else 0.0

    # Use discretization margin: err_N = |price(N)-price(2N)|
    inp_500 = PricingInput(float(S), float(K), float(T), float(r), float(q), float(sigma), bool(option_is_call))
    a_500 = price_american_binomial_crr(inp_500, steps=500)
    a_1000 = price_american_binomial_crr(inp_500, steps=1000)
    a_2000 = price_american_binomial_crr(inp_500, steps=2000)
    a_4000 = price_american_binomial_crr(inp_500, steps=4000)
    err_500 = abs(a_500 - a_1000)
    err_1000 = abs(a_1000 - a_2000)
    err_2000 = abs(a_2000 - a_4000)

    opt_type = "call" if option_is_call else "put"
    e_price = bs_price(opt_type, float(S), float(K), float(r), float(q), float(sigma), float(T))

    # Enforce: american price at N (or 2N) plus discretization error >= european price
    # consider 3 levels of discretization margin (N,2N,4N)
    # use a small integer multiplier on the discretization error to be conservative
    assert max(a_500 + 4 * err_500, a_1000 + 4 * err_1000, a_2000 + 4 * err_2000) >= e_price


def test_no_dividend_call_equals_european():
    # For q=0, American call should equal European call within SSOT tolerances
    S = 100.0
    K = 100.0
    T = 1.0
    sigma = 0.25
    r = 0.02
    q = 0.0
    inp_500 = PricingInput(float(S), float(K), float(T), float(r), float(q), float(sigma), True)
    a_500 = price_american_binomial_crr(inp_500, steps=500)
    a_1000 = price_american_binomial_crr(inp_500, steps=1000)
    a_2000 = price_american_binomial_crr(inp_500, steps=2000)
    a_4000 = price_american_binomial_crr(inp_500, steps=4000)
    err_500 = abs(a_500 - a_1000)
    err_1000 = abs(a_1000 - a_2000)
    err_2000 = abs(a_2000 - a_4000)
    e_price = bs_price("call", float(S), float(K), float(r), float(q), float(sigma), float(T))

    # Allow equality within discretization margin (integer multiplier on err_N). Prefer the largest-step estimate.
    assert abs(a_2000 - e_price) <= 4 * err_2000


def test_convergence_steps():
    # Stability: price should converge as steps increase
    S = 100.0
    K = 95.0
    T = 1.0
    sigma = 0.25
    r = 0.01
    q = 0.0
    def make_inp(steps: int) -> PricingInput:
        return PricingInput(float(S), float(K), float(T), float(r), float(q), float(sigma), True)

    p_250 = price_american_binomial_crr(make_inp(250), steps=250)
    p_500 = price_american_binomial_crr(make_inp(500), steps=500)
    p_1000 = price_american_binomial_crr(make_inp(1000), steps=1000)

    # Shrinking-error invariant: err_500_1000 <= err_250_500
    err_250_500 = abs(p_250 - p_500)
    err_500_1000 = abs(p_500 - p_1000)
    assert err_500_1000 <= err_250_500, f"Error did not shrink: {err_500_1000} > {err_250_500}"
