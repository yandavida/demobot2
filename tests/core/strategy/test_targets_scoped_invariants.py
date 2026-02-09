import pytest

from core.strategy.targets import PortfolioTargets, ScopedTargets


def test_rejects_empty_strategy_id():
    with pytest.raises(ValueError):
        ScopedTargets(overrides={"": PortfolioTargets(delta=0.0)})
    with pytest.raises(ValueError):
        ScopedTargets(overrides={"   ": PortfolioTargets(delta=0.0)})


def test_accepts_valid_strategy_ids_and_overrides():
    s = ScopedTargets(baseline=PortfolioTargets(delta=1.0), overrides={"stratA": PortfolioTargets(delta=None, vega=0.5)})
    assert "stratA" in s.overrides
    assert s.overrides["stratA"].vega == 0.5


def test_rejects_nan_and_infinite_in_overrides():
    with pytest.raises(ValueError):
        ScopedTargets(overrides={"s": PortfolioTargets(delta=float("nan"))})


def test_permutation_invariant_equality_and_deterministic_repr():
    a = [("b", PortfolioTargets(delta=1.0)), ("a", PortfolioTargets(delta=2.0))]
    b = [("a", PortfolioTargets(delta=2.0)), ("b", PortfolioTargets(delta=1.0))]

    s1 = ScopedTargets(overrides=dict(a))
    s2 = ScopedTargets(overrides=dict(b))

    assert s1 == s2
    # repr must be stable/deterministic (sorted by strategy id)
    r1 = repr(s1)
    r2 = repr(s2)
    assert r1 == r2


def test_absence_means_no_scoped_targets():
    s = ScopedTargets()
    assert s.baseline is None
    assert s.overrides == {}
