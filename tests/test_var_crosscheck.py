import pytest
from statistics import pstdev
from core.risk.var_parametric import calc_parametric_var
from core.risk.var_historical import calc_historical_var

def make_quasi_normal_series(s=10.0, M=50):
    # values and weights (Pascal-like)
    values = [-3, -2, -1, 0, 1, 2, 3]
    weights = [1, 6, 15, 20, 15, 6, 1]
    series = []
    for v, w in zip(values, weights):
        series.extend([v * s] * (w * M))
    return series

def test_var_crosscheck_99():
    pnl_series = make_quasi_normal_series(s=10.0, M=50)
    sigma_emp = pstdev(pnl_series)
    var_param = calc_parametric_var(sigma_pv_1d=sigma_emp, confidence=0.99, horizon_days=1)
    var_hist = calc_historical_var(pnl_series=pnl_series, confidence=0.99)
    assert var_hist > 0
    assert var_param > 0
    ratio = var_hist / var_param
    assert 0.5 <= ratio <= 1.5

def test_var_crosscheck_95():
    pnl_series = make_quasi_normal_series(s=10.0, M=50)
    sigma_emp = pstdev(pnl_series)
    var_param = calc_parametric_var(sigma_pv_1d=sigma_emp, confidence=0.95, horizon_days=1)
    var_hist = calc_historical_var(pnl_series=pnl_series, confidence=0.95)
    assert var_hist > 0
    assert var_param > 0
    ratio = var_hist / var_param
    assert 0.5 <= ratio <= 1.6

def test_var_scaling_invariance():
    pnl_series = make_quasi_normal_series(s=10.0, M=50)
    sigma_emp = pstdev(pnl_series)
    var_param = calc_parametric_var(sigma_pv_1d=sigma_emp, confidence=0.99, horizon_days=1)
    var_hist = calc_historical_var(pnl_series=pnl_series, confidence=0.99)
    k = 2.0
    pnl_series2 = [k * x for x in pnl_series]
    sigma_emp2 = pstdev(pnl_series2)
    var_param2 = calc_parametric_var(sigma_pv_1d=sigma_emp2, confidence=0.99, horizon_days=1)
    var_hist2 = calc_historical_var(pnl_series=pnl_series2, confidence=0.99)
    assert var_param2 == pytest.approx(k * var_param, rel=1e-12)
    assert var_hist2 == pytest.approx(k * var_hist, rel=1e-12)
