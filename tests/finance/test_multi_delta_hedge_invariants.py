from __future__ import annotations

import pytest

from core.numeric_policy import DEFAULT_TOLERANCES, MetricClass


# Try to import the intended future primitive. If missing, skip the tests explicitly.
try:
    from core.hedging.primitives import multi_delta_hedge  # type: ignore
except Exception:  # pragma: no cover - skip when not present
    multi_delta_hedge = None  # type: ignore


def require_impl():
    if multi_delta_hedge is None:
        pytest.skip("multi_delta_hedge not implemented in core.hedging.primitives - skipping F5.4 tests")


def approx_list(a, b):
    tol = DEFAULT_TOLERANCES[MetricClass.DELTA]
    return all(pytest.approx(x, rel=tol.rel, abs=tol.abs) == y for x, y in zip(a, b))


def test_linearity_in_dp_or_skip():
    require_impl()
    deltas = [0.5, -0.25]
    dp_a = 0.3
    dp_b = 0.2

    q_a, r_a = multi_delta_hedge(dp_a, deltas)
    q_b, r_b = multi_delta_hedge(dp_b, deltas)

    q_comb, r_comb = multi_delta_hedge(dp_a + dp_b, deltas)

    # Elementwise linearity in hedge quantities and additivity in residuals
    assert approx_list(q_comb, [qa + qb for qa, qb in zip(q_a, q_b)])
    assert pytest.approx(r_comb, rel=DEFAULT_TOLERANCES[MetricClass.DELTA].rel, abs=DEFAULT_TOLERANCES[MetricClass.DELTA].abs) == (r_a + r_b)


def test_residual_correctness_and_permutation_invariance_or_skip():
    require_impl()
    deltas = [0.4, -0.2, 0.3]
    dp = 0.6

    q, residual = multi_delta_hedge(dp, deltas)

    # residual should equal dp - sum(q_i * delta_i)
    recomputed = dp - sum(qi * di for qi, di in zip(q, deltas))
    assert pytest.approx(residual, rel=DEFAULT_TOLERANCES[MetricClass.DELTA].rel, abs=DEFAULT_TOLERANCES[MetricClass.DELTA].abs) == recomputed

    # Permutation invariance: permute deltas and ensure quantities permute accordingly
    perm = [2, 0, 1]
    deltas_perm = [deltas[i] for i in perm]
    q_perm, residual_perm = multi_delta_hedge(dp, deltas_perm)
    q_reordered = [q[i] for i in perm]
    assert approx_list(q_perm, q_reordered)
    assert pytest.approx(residual_perm, rel=DEFAULT_TOLERANCES[MetricClass.DELTA].rel, abs=DEFAULT_TOLERANCES[MetricClass.DELTA].abs) == residual


def test_guards_and_determinism_or_skip():
    require_impl()
    # Guard: any delta_i == 0 should raise deterministic error
    deltas_bad = [0.2, 0.0]
    with pytest.raises(Exception):
        multi_delta_hedge(0.1, deltas_bad)

    # Determinism: same inputs -> identical outputs
    deltas = [0.25, -0.1]
    dp = 0.33
    out1 = multi_delta_hedge(dp, deltas)
    out2 = multi_delta_hedge(dp, deltas)
    # exact equality expected for deterministic pure function
    assert out1 == out2
