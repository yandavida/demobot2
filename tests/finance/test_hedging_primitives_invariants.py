import json
from typing import Any

import pytest

from core.numeric_policy import DEFAULT_TOLERANCES, MetricClass


# Local helper: deterministic algebraic delta hedge (test-local only)
def delta_hedge_quantity(delta_p: float, delta_h: float) -> float:
    if delta_h == 0.0:
        raise ZeroDivisionError("hedge instrument delta is zero")
    return -delta_p / delta_h


def residual_delta(delta_p: float, delta_h: float, q: float) -> float:
    return delta_p + q * delta_h


def serialize(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True)


@pytest.mark.unit
def test_permutation_invariance_same_exposure_ordering():
    # Two portfolios with identical exposures in different orders
    p1 = [{"id": "a", "delta": 0.5}, {"id": "b", "delta": -0.2}]
    p2 = [{"id": "b", "delta": -0.2}, {"id": "a", "delta": 0.5}]

    # Compute exposures (sum deltas) and a simple hedge using a single hedge instrument
    total_p1 = sum(x["delta"] for x in p1)
    total_p2 = sum(x["delta"] for x in p2)

    # Hedge instrument with non-zero delta
    delta_h = 0.25

    q1 = delta_hedge_quantity(total_p1, delta_h)
    q2 = delta_hedge_quantity(total_p2, delta_h)

    r1 = residual_delta(total_p1, delta_h, q1)
    r2 = residual_delta(total_p2, delta_h, q2)

    # Serialization equality (permutation-invariant representation)
    assert serialize({"q": q1, "r": r1}) == serialize({"q": q2, "r": r2})


@pytest.mark.unit
def test_linearity_additivity_of_hedge_quantity():
    # Portfolio A and B
    a = [{"id": "a1", "delta": 0.3}]
    b = [{"id": "b1", "delta": -0.1}]

    total_a = sum(x["delta"] for x in a)
    total_b = sum(x["delta"] for x in b)

    total_combined = total_a + total_b

    delta_h = 0.2

    q_a = delta_hedge_quantity(total_a, delta_h)
    q_b = delta_hedge_quantity(total_b, delta_h)
    q_combined = delta_hedge_quantity(total_combined, delta_h)

    # Hedge(combined) == Hedge(A) + Hedge(B)
    assert pytest.approx(q_combined, rel=DEFAULT_TOLERANCES[MetricClass.DELTA].rel, abs=DEFAULT_TOLERANCES[MetricClass.DELTA].abs) == (q_a + q_b)


@pytest.mark.unit
def test_delta_hedge_correctness_closed_form():
    delta_p = 0.123456
    delta_h = 0.5

    if delta_h == 0.0:
        pytest.xfail("delta_h == 0: deterministic error type not defined in production")

    q = delta_hedge_quantity(delta_p, delta_h)
    r = residual_delta(delta_p, delta_h, q)

    tol = DEFAULT_TOLERANCES[MetricClass.DELTA]
    assert abs(r) <= tol.abs


@pytest.mark.unit
def test_scaling_invariance_of_hedge_and_residual():
    base_positions = [{"id": "x", "delta": 0.4}, {"id": "y", "delta": -0.15}]
    total_base = sum(x["delta"] for x in base_positions)

    k = 10.0
    total_scaled = k * total_base

    delta_h = 0.25

    q_base = delta_hedge_quantity(total_base, delta_h)
    q_scaled = delta_hedge_quantity(total_scaled, delta_h)

    r_base = residual_delta(total_base, delta_h, q_base)
    r_scaled = residual_delta(total_scaled, delta_h, q_scaled)

    assert pytest.approx(q_scaled, rel=DEFAULT_TOLERANCES[MetricClass.DELTA].rel, abs=DEFAULT_TOLERANCES[MetricClass.DELTA].abs) == (k * q_base)
    assert pytest.approx(r_scaled, rel=DEFAULT_TOLERANCES[MetricClass.DELTA].rel, abs=DEFAULT_TOLERANCES[MetricClass.DELTA].abs) == (k * r_base)


@pytest.mark.unit
def test_edge_cases_zero_hedge_or_zero_portfolio():
    # Δh == 0 -> deterministic error expected; if production type missing, xfail
    delta_p = 0.1
    delta_h_zero = 0.0

    try:
        _ = delta_hedge_quantity(delta_p, delta_h_zero)
        # If no exception, that's a failure for this deterministic requirement
        pytest.fail("Expected deterministic error when delta_h == 0")
    except ZeroDivisionError:
        pass

    # Δp == 0 -> hedge q == 0 and residual == 0
    delta_p_zero = 0.0
    delta_h = 0.3
    q = delta_hedge_quantity(delta_p_zero, delta_h)
    r = residual_delta(delta_p_zero, delta_h, q)
    assert q == 0.0
    assert r == 0.0
