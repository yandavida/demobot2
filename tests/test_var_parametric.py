import math
import pytest
from core.risk.var_parametric import calc_parametric_var

def test_var_zero_confidence_approx():
    # confidence=0.5 → z≈0 so VaR≈0
    v = calc_parametric_var(sigma_pv_1d=1.0, confidence=0.5, horizon_days=1)
    assert abs(v) < 1e-8

def test_var_monotonicity():
    # higher confidence → higher VaR
    v1 = calc_parametric_var(sigma_pv_1d=2.0, confidence=0.95, horizon_days=1)
    v2 = calc_parametric_var(sigma_pv_1d=2.0, confidence=0.99, horizon_days=1)
    assert v2 > v1

def test_var_horizon_scaling():
    # horizon 10d vs 1d scales by sqrt(10)
    v1 = calc_parametric_var(sigma_pv_1d=3.0, confidence=0.99, horizon_days=1)
    v10 = calc_parametric_var(sigma_pv_1d=3.0, confidence=0.99, horizon_days=10)
    assert math.isclose(v10, v1 * math.sqrt(10), rel_tol=1e-9)

def test_var_sigma_zero():
    # sigma=0 → VaR=0
    v = calc_parametric_var(sigma_pv_1d=0.0, confidence=0.99, horizon_days=1)
    assert v == 0.0

def test_var_invalid_horizon():
    with pytest.raises(ValueError):
        calc_parametric_var(sigma_pv_1d=1.0, confidence=0.99, horizon_days=0)
    with pytest.raises(ValueError):
        calc_parametric_var(sigma_pv_1d=1.0, confidence=0.99, horizon_days=-5)

def test_var_invalid_sigma():
    with pytest.raises(ValueError):
        calc_parametric_var(sigma_pv_1d=-1.0, confidence=0.99, horizon_days=1)

def test_var_invalid_confidence():
    with pytest.raises(ValueError):
        calc_parametric_var(sigma_pv_1d=1.0, confidence=0.0, horizon_days=1)
    with pytest.raises(ValueError):
        calc_parametric_var(sigma_pv_1d=1.0, confidence=1.0, horizon_days=1)
