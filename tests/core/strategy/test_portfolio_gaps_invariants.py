import pytest

from core.strategy.gaps import (
    PortfolioExposures,
    compute_portfolio_gaps,
)
from core.strategy.targets import PortfolioTargets
from core.numeric_policy import DEFAULT_TOLERANCES, MetricClass


def test_gap_is_none_when_target_none():
    current = PortfolioExposures(delta=10.0, gamma=1.0, vega=0.5)
    targets = PortfolioTargets(delta=None, gamma=None, vega=None)
    gaps = compute_portfolio_gaps(current, targets)
    assert gaps.delta is None
    assert gaps.gamma is None
    assert gaps.vega is None


def test_gap_arithmetic_when_target_set():
    current = PortfolioExposures(delta=5.0, gamma=0.5, vega=0.1)
    targets = PortfolioTargets(delta=8.0, gamma=0.0, vega=0.3)
    gaps = compute_portfolio_gaps(current, targets)
    tol = DEFAULT_TOLERANCES[MetricClass.PNL].abs
    assert abs(gaps.delta - 3.0) <= tol
    assert abs(gaps.gamma - (-0.5)) <= tol
    assert abs(gaps.vega - 0.2) <= tol


def test_idempotence_and_determinism():
    current = PortfolioExposures(delta=1.0, gamma=2.0, vega=3.0)
    targets = PortfolioTargets(delta=2.0, gamma=None, vega=1.0)
    g1 = compute_portfolio_gaps(current, targets)
    g2 = compute_portfolio_gaps(current, targets)
    assert g1 == g2


def test_monotonicity_closer_to_target():
    targets = PortfolioTargets(delta=10.0)
    c_far = PortfolioExposures(delta=0.0)
    c_closer = PortfolioExposures(delta=8.0)
    gap_far = compute_portfolio_gaps(c_far, targets).delta
    gap_closer = compute_portfolio_gaps(c_closer, targets).delta
    assert gap_far is not None and gap_closer is not None
    tol = DEFAULT_TOLERANCES[MetricClass.PNL].abs
    assert abs(gap_closer) <= abs(gap_far) + tol


def test_rejects_non_finite_current_exposures():
    # construction of non-finite exposures must be rejected
    with pytest.raises(ValueError):
        PortfolioExposures(delta=float("nan"))
