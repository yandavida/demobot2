import pytest
from core.risk.var_historical import calc_historical_var

def make_sample():
    # [-10, -5, -1, 0, 1, 5, 10] * 10 = n=70
    return [-10, -5, -1, 0, 1, 5, 10] * 10

def test_basic_correctness():
    pnl_series = make_sample()
    n = len(pnl_series)
    confidence = 0.9
    alpha = 1.0 - confidence
    sorted_pnl = sorted(pnl_series)
    idx = max(0, min(n - 1, int((alpha * n + 0.9999)) - 1))  # ceil(alpha*n)-1
    q = sorted_pnl[idx]
    expected_var = max(0.0, -q)
    var = calc_historical_var(pnl_series=pnl_series, confidence=confidence)
    assert var == expected_var

def test_monotonicity():
    pnl_series = make_sample()
    v90 = calc_historical_var(pnl_series=pnl_series, confidence=0.90)
    v95 = calc_historical_var(pnl_series=pnl_series, confidence=0.95)
    v99 = calc_historical_var(pnl_series=pnl_series, confidence=0.99)
    assert v99 >= v95 >= v90

def test_all_gains():
    pnl_series = [1, 2, 3, 4, 5] * 20  # n=100
    var = calc_historical_var(pnl_series=pnl_series, confidence=0.99)
    assert var == 0.0

def test_too_short_series():
    with pytest.raises(ValueError):
        calc_historical_var(pnl_series=[1.0]*19, confidence=0.95)

def test_invalid_confidence():
    pnl_series = make_sample()
    with pytest.raises(ValueError):
        calc_historical_var(pnl_series=pnl_series, confidence=0.5)
    with pytest.raises(ValueError):
        calc_historical_var(pnl_series=pnl_series, confidence=1.0)
