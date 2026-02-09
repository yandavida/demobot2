import math
import pytest

from core.strategy.targets import PortfolioTargets


def test_accepts_none_and_finite_floats():
    t = PortfolioTargets(delta=None, gamma=0.0, vega=1.23)
    assert t.delta is None
    assert math.isfinite(t.gamma)
    assert math.isfinite(t.vega)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf")])
def test_rejects_nan_and_infinite(bad):
    with pytest.raises(ValueError):
        PortfolioTargets(delta=bad)
    with pytest.raises(ValueError):
        PortfolioTargets(gamma=bad)
    with pytest.raises(ValueError):
        PortfolioTargets(vega=bad)


def test_unset_vs_zero_is_distinct():
    a = PortfolioTargets(delta=None)
    b = PortfolioTargets(delta=0.0)
    assert a.delta is None
    assert b.delta == 0.0
    assert a != b


def test_repr_and_equality_roundtrip():
    t1 = PortfolioTargets(delta=1.0, gamma=2.0, vega=None)
    t2 = PortfolioTargets(delta=1.0, gamma=2.0, vega=None)
    assert t1 == t2
    r = repr(t1)
    assert "PortfolioTargets" in r
