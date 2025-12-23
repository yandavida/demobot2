import pytest
from core.risk.var_historical import calc_historical_var, calc_cvar_expected_shortfall
from core.risk.var_parametric import calc_parametric_var

def test_sample_size_boundary():
    series19 = [-1] * 19
    series20 = [-1] * 20
    # len 19 should raise
    with pytest.raises(ValueError):
        calc_historical_var(pnl_series=series19, confidence=0.95)
    with pytest.raises(ValueError):
        calc_cvar_expected_shortfall(pnl_series=series19, confidence=0.95)
    # len 20 should work
    v = calc_historical_var(pnl_series=series20, confidence=0.95)
    c = calc_cvar_expected_shortfall(pnl_series=series20, confidence=0.95)
    assert v == 1.0
    assert c == 1.0

def test_constant_series_losses():
    series = [-2.5] * 100
    for conf in (0.9, 0.99):
        v = calc_historical_var(pnl_series=series, confidence=conf)
        c = calc_cvar_expected_shortfall(pnl_series=series, confidence=conf)
        assert v == 2.5
        assert c == 2.5

def test_constant_series_gains():
    series = [2.5] * 100
    for conf in (0.9, 0.99):
        v = calc_historical_var(pnl_series=series, confidence=conf)
        c = calc_cvar_expected_shortfall(pnl_series=series, confidence=conf)
        assert v == 0.0
        assert c == 0.0

def test_confidence_validation():
    series = [-1] * 30
    for fn in (calc_historical_var, calc_cvar_expected_shortfall):
        for bad_conf in (0.5, 1.0, -0.1):
            with pytest.raises(ValueError):
                fn(pnl_series=series, confidence=bad_conf)
    # parametric VaR: 0.5 is allowed and yields ~0
    var = calc_parametric_var(sigma_pv_1d=10, confidence=0.5, horizon_days=1)
    assert var == pytest.approx(0.0, abs=1e-6)
    for bad_conf in (1.0, -0.1):
        with pytest.raises(ValueError):
            calc_parametric_var(sigma_pv_1d=1.0, confidence=bad_conf, horizon_days=1)

def test_parametric_var_boundaries():
    # sigma=0 => VaR=0
    for conf in (0.9, 0.99):
        v = calc_parametric_var(sigma_pv_1d=0.0, confidence=conf, horizon_days=1)
        assert v == 0.0
    # horizon_days <= 0 raises
    with pytest.raises(ValueError):
        calc_parametric_var(sigma_pv_1d=1.0, confidence=0.99, horizon_days=0)
    with pytest.raises(ValueError):
        calc_parametric_var(sigma_pv_1d=1.0, confidence=0.99, horizon_days=-1)
    # confidence ~0.5 yields ~0
    v = calc_parametric_var(sigma_pv_1d=10, confidence=0.5000001, horizon_days=1)
    assert v == pytest.approx(0, abs=1e-3)

def test_determinism_idempotence():
    series = [-2, -1, 0, 1, 2] * 10
    for conf in (0.9, 0.95, 0.99):
        v1 = calc_historical_var(pnl_series=series, confidence=conf)
        v2 = calc_historical_var(pnl_series=series, confidence=conf)
        c1 = calc_cvar_expected_shortfall(pnl_series=series, confidence=conf)
        c2 = calc_cvar_expected_shortfall(pnl_series=series, confidence=conf)
        assert v1 == v2
        assert c1 == c2
