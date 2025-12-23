import pytest
from core.risk.var_historical import calc_cvar_expected_shortfall, calc_historical_var
import math

def make_sample():
    # [-10, -5, -1, 0, 1, 5, 10] * 5 = n=35
    return [-10, -5, -1, 0, 1, 5, 10] * 5

def test_cvar_controlled_correctness():
    pnl_series = make_sample()
    n = len(pnl_series)
    confidence = 0.9
    alpha = 1.0 - confidence
    sorted_pnl = sorted(pnl_series)
    k = math.ceil(alpha * n) - 1
    k = max(0, min(n - 1, k))
    q = sorted_pnl[k]
    tail = [x for x in pnl_series if x <= q]
    expected_cvar = max(0.0, -sum(tail) / len(tail))
    cvar = calc_cvar_expected_shortfall(pnl_series=pnl_series, confidence=confidence)
    assert math.isclose(cvar, expected_cvar, rel_tol=1e-12)

def test_cvar_ge_var():
    pnl_series = make_sample()
    confidence = 0.95
    cvar = calc_cvar_expected_shortfall(pnl_series=pnl_series, confidence=confidence)
    var = calc_historical_var(pnl_series=pnl_series, confidence=confidence)
    assert cvar >= var

def test_cvar_monotonicity():
    pnl_series = make_sample()
    c90 = calc_cvar_expected_shortfall(pnl_series=pnl_series, confidence=0.90)
    c95 = calc_cvar_expected_shortfall(pnl_series=pnl_series, confidence=0.95)
    c99 = calc_cvar_expected_shortfall(pnl_series=pnl_series, confidence=0.99)
    assert c99 >= c95 >= c90

def test_cvar_all_gains():
    pnl_series = [1, 2, 3, 4, 5] * 10  # n=50
    cvar = calc_cvar_expected_shortfall(pnl_series=pnl_series, confidence=0.99)
    assert cvar == 0.0

def test_cvar_too_short_series():
    with pytest.raises(ValueError):
        calc_cvar_expected_shortfall(pnl_series=[1.0]*19, confidence=0.95)

def test_cvar_invalid_confidence():
    pnl_series = make_sample()
    with pytest.raises(ValueError):
        calc_cvar_expected_shortfall(pnl_series=pnl_series, confidence=0.5)
    with pytest.raises(ValueError):
        calc_cvar_expected_shortfall(pnl_series=pnl_series, confidence=1.0)
