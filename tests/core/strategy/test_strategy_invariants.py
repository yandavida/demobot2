import copy
from typing import Tuple

from core.strategy.gaps import compute_portfolio_gaps, PortfolioExposures
from core.strategy.scoped_gaps import compute_scoped_gaps
from core.strategy.targets import PortfolioTargets, ScopedTargets
from core.numeric_policy import DEFAULT_TOLERANCES, MetricClass


def _serialize_portfolio_gap(g):
    return (g.delta, g.gamma, g.vega)


def _serialize_scoped_gaps(d: dict) -> Tuple[Tuple[str, Tuple[object, object, object]], ...]:
    # canonical serialization: sort by strategy id
    return tuple(sorted(((sid, _serialize_portfolio_gap(g)) for sid, g in d.items()), key=lambda x: x[0]))


def test_permutation_invariance_scoped_and_portfolio():
    # scoped: ordering of current mapping and overrides should not affect result
    current_a = {"a": PortfolioExposures(delta=1.0), "b": PortfolioExposures(delta=2.0)}
    current_b = {"b": PortfolioExposures(delta=2.0), "a": PortfolioExposures(delta=1.0)}

    overrides1 = {"a": PortfolioTargets(delta=5.0), "b": PortfolioTargets(delta=3.0)}
    overrides2 = {"b": PortfolioTargets(delta=3.0), "a": PortfolioTargets(delta=5.0)}

    s1 = compute_scoped_gaps(current_a, ScopedTargets(overrides=overrides1))
    s2 = compute_scoped_gaps(current_b, ScopedTargets(overrides=overrides2))
    assert _serialize_scoped_gaps(s1) == _serialize_scoped_gaps(s2)

    # portfolio: inputs are scalars/dataclasses; repeated calls equal
    cur = PortfolioExposures(delta=10.0)
    t = PortfolioTargets(delta=15.0)
    p1 = compute_portfolio_gaps(cur, t)
    p2 = compute_portfolio_gaps(cur, t)
    assert _serialize_portfolio_gap(p1) == _serialize_portfolio_gap(p2)


def test_idempotence():
    cur = PortfolioExposures(delta=4.0)
    t = PortfolioTargets(delta=10.0)
    p1 = compute_portfolio_gaps(cur, t)
    p2 = compute_portfolio_gaps(cur, t)
    assert p1 == p2

    current = {"s": PortfolioExposures(delta=1.0)}
    scoped = ScopedTargets(overrides={"s": PortfolioTargets(delta=2.0)})
    s1 = compute_scoped_gaps(current, scoped)
    s2 = compute_scoped_gaps(current, scoped)
    assert s1 == s2


def test_monotonicity_portfolio_and_scoped():
    tol = DEFAULT_TOLERANCES[MetricClass.PNL].abs

    # portfolio monotonicity
    t = PortfolioTargets(delta=10.0)
    cur_far = PortfolioExposures(delta=0.0)
    cur_closer = PortfolioExposures(delta=8.0)
    gap_far = compute_portfolio_gaps(cur_far, t).delta
    gap_closer = compute_portfolio_gaps(cur_closer, t).delta
    assert abs(gap_closer) <= abs(gap_far) + tol

    # scoped monotonicity
    current_far = {"s": PortfolioExposures(delta=0.0)}
    current_closer = {"s": PortfolioExposures(delta=9.0)}
    scoped = ScopedTargets(overrides={"s": PortfolioTargets(delta=10.0)})
    gap_far_s = compute_scoped_gaps(current_far, scoped)["s"].delta
    gap_closer_s = compute_scoped_gaps(current_closer, scoped)["s"].delta
    assert abs(gap_closer_s) <= abs(gap_far_s) + tol


def test_scope_isolation():
    # changing portfolio target should not change scoped gaps
    current = {"s": PortfolioExposures(delta=1.0)}
    scoped = ScopedTargets(overrides={"s": PortfolioTargets(delta=3.0)})

    scoped_before = compute_scoped_gaps(current, scoped)
    # mutate portfolio targets
    portfolio_t1 = PortfolioTargets(delta=100.0)
    _ = compute_portfolio_gaps(PortfolioExposures(delta=0.0), portfolio_t1)
    scoped_after = compute_scoped_gaps(current, scoped)
    assert _serialize_scoped_gaps(scoped_before) == _serialize_scoped_gaps(scoped_after)

    # changing scoped targets should not change portfolio gaps
    p_before = compute_portfolio_gaps(PortfolioExposures(delta=2.0), PortfolioTargets(delta=5.0))
    _ = compute_scoped_gaps(current, ScopedTargets(overrides={"s": PortfolioTargets(delta=9.0)}))
    p_after = compute_portfolio_gaps(PortfolioExposures(delta=2.0), PortfolioTargets(delta=5.0))
    assert _serialize_portfolio_gap(p_before) == _serialize_portfolio_gap(p_after)


def test_none_semantics_preservation_and_determinism():
    # None target => None gap
    cur = PortfolioExposures(delta=1.0)
    t = PortfolioTargets(delta=None)
    p = compute_portfolio_gaps(cur, t)
    assert p.delta is None

    current = {"s": PortfolioExposures(delta=1.0)}
    scoped = ScopedTargets(overrides={"s": PortfolioTargets(delta=None)})
    out = compute_scoped_gaps(current, scoped)
    assert out["s"].delta is None

    # repeated calls and permutations preserve None semantics
    out1 = compute_scoped_gaps(copy.deepcopy(current), ScopedTargets(overrides={"s": PortfolioTargets(delta=None)}))
    out2 = compute_scoped_gaps(current, ScopedTargets(overrides={"s": PortfolioTargets(delta=None)}))
    assert out1 == out2


def test_deterministic_snapshot_equality():
    current = {"a": PortfolioExposures(delta=1.0), "b": PortfolioExposures(delta=2.0)}
    scoped = ScopedTargets(overrides={"a": PortfolioTargets(delta=3.0), "b": PortfolioTargets(delta=4.0)})
    out = compute_scoped_gaps(current, scoped)
    # structural snapshot (canonical) must be stable
    snap1 = _serialize_scoped_gaps(out)
    snap2 = _serialize_scoped_gaps(out)
    assert snap1 == snap2
