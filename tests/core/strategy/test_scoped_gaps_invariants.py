import pytest

from core.strategy.scoped_gaps import compute_scoped_gaps
from core.strategy.gaps import PortfolioExposures
from core.strategy.targets import ScopedTargets, PortfolioTargets


def test_no_emitted_gaps_when_no_scoped_target_for_strategy():
    current = {"s1": PortfolioExposures(delta=1.0)}
    scoped = ScopedTargets()
    out = compute_scoped_gaps(current, scoped)
    assert out == {}


def test_arithmetic_per_strategy_and_none_semantics():
    current = {
        "sA": PortfolioExposures(delta=2.0, gamma=0.1, vega=0.0),
        "sB": PortfolioExposures(delta=5.0, gamma=0.0, vega=1.0),
    }
    scoped = ScopedTargets(overrides={
        "sA": PortfolioTargets(delta=3.0, gamma=None, vega=0.5),
        "sB": PortfolioTargets(delta=None, gamma=1.0, vega=None),
    })

    gaps = compute_scoped_gaps(current, scoped)
    assert isinstance(gaps, dict)
    assert "sA" in gaps and "sB" in gaps
    assert gaps["sA"].delta == pytest.approx(1.0)
    assert gaps["sA"].gamma is None
    assert gaps["sB"].delta is None


def test_determinism_and_permutation_invariance():
    current = {"a": PortfolioExposures(delta=0.0), "b": PortfolioExposures(delta=1.0)}
    scoped = ScopedTargets(overrides={"b": PortfolioTargets(delta=5.0), "a": PortfolioTargets(delta=2.0)})
    out1 = compute_scoped_gaps(current, scoped)
    # reorder inputs
    current2 = {k: current[k] for k in reversed(list(current.keys()))}
    scoped2 = ScopedTargets(overrides={"a": PortfolioTargets(delta=2.0), "b": PortfolioTargets(delta=5.0)})
    out2 = compute_scoped_gaps(current2, scoped2)
    assert out1 == out2


def test_rejects_non_finite_values_in_inputs():
    # construction of non-finite exposures should be rejected
    with pytest.raises(ValueError):
        PortfolioExposures(delta=float("nan"))
