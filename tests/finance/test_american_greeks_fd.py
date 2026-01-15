from __future__ import annotations

from core.pricing.american_greeks import american_price_greeks_fd
from core.numeric_policy import DEFAULT_TOLERANCES, MetricClass


PRICE_TOL = DEFAULT_TOLERANCES[MetricClass.PRICE]
DELTA_TOL = DEFAULT_TOLERANCES[MetricClass.DELTA]


def _assert_close_price(a: float, b: float, multiplier: int = 1) -> None:
    abs_tol = PRICE_TOL.abs or 0.0
    rel_tol = PRICE_TOL.rel or 0.0
    limit = multiplier * max(abs_tol, rel_tol * max(abs(a), abs(b), 1.0))
    assert abs(a - b) <= limit, f"Price mismatch: |{a}-{b}| > {limit}"


def test_repeatable_determinism():
    params = dict(s=100.0, k=95.0, t=1.0, sigma=0.25, r=0.01, q=0.0, is_call=True, steps=500)
    g1 = american_price_greeks_fd(**params)
    g2 = american_price_greeks_fd(**params)
    assert g1 == g2


def test_basic_signs_and_units():
    out = american_price_greeks_fd(s=100.0, k=100.0, t=0.5, sigma=0.2, r=0.01, q=0.0, is_call=True, steps=500)
    # delta in (0,1)
    assert out["delta"] > - (DELTA_TOL.abs or 0.0)
    assert out["delta"] < 1.0 + (DELTA_TOL.abs or 0.0)
    # gamma non-negative
    assert out["gamma"] >= - (PRICE_TOL.abs or 0.0)
    # vega non-negative
    assert out["vega"] >= - (PRICE_TOL.abs or 0.0)
    # theta typically non-positive for q=0
    assert out["theta"] <= (PRICE_TOL.abs or 0.0)
    # rho for call with q=0 non-negative
    assert out["rho"] >= - (PRICE_TOL.abs or 0.0)


def test_gamma_delta_consistency():
    # Check gamma ≈ d(delta)/dS using the same deterministic hS logic inside helper
    params = dict(s=110.0, k=100.0, t=0.5, sigma=0.25, r=0.01, q=0.0, is_call=True, steps=500)
    out = american_price_greeks_fd(**params)
    # central-difference delta-based gamma approximation
    s = params["s"]
    # replicate hS used by implementation
    hS = max(round(s * 0.001, 2), 0.01)
    p_plus = american_price_greeks_fd(**{**params, "s": s + hS})
    p_minus = american_price_greeks_fd(**{**params, "s": s - hS})
    gamma_from_deltas = (p_plus["delta"] - p_minus["delta"]) / (2.0 * hS)

    # numerical FD methods may differ in discretization error; require sign agreement
    # and a reasonable relative agreement (within 50%) to catch gross mismatches.
    a = out["gamma"]
    b = gamma_from_deltas
    assert (a >= 0 and b >= 0) or (a <= 0 and b <= 0)
    rel_diff = abs(a - b) / max(abs(a), abs(b), 1.0)
    assert rel_diff <= 0.5, f"Gamma relative difference too large: {rel_diff}"


def test_vega_unit_consistency():
    # vega returned is per 1% IV; verify by recomputing vega_abs and comparing
    params = dict(s=100.0, k=95.0, t=1.0, sigma=0.2, r=0.01, q=0.0, is_call=True, steps=500)
    out = american_price_greeks_fd(**params)
    # recompute vega_abs by central difference with hV = 0.001
    hV = 0.001
    p_plus = american_price_greeks_fd(**{**params, "sigma": params["sigma"] + hV})["price"]
    p_minus = american_price_greeks_fd(**{**params, "sigma": max(params["sigma"] - hV, DEFAULT_TOLERANCES[MetricClass.VOL].abs or 0.0)})["price"]
    vega_abs = (p_plus - p_minus) / (2.0 * hV)
    # vega returned should be vega_abs / 100.0 (per 1% IV)
    _assert_close_price(out["vega"] * 100.0, vega_abs, multiplier=4)
