import pytest
from core.risk.var_historical import calc_historical_var, calc_cvar_expected_shortfall

# Dataset A: mixed
base_a = [-10, -5, -1, 0, 1, 5, 10]
dataset_a = base_a * 30  # n=210
# Dataset B: heavy loss tail
dataset_b = [-100]*30 + [-10]*30 + [0]*30 + [10]*30  # n=120
# Dataset C: all gains
dataset_c = [1, 2, 3, 4, 5] * 30  # n=150

confidences = [0.9, 0.95, 0.99]

def test_non_negativity():
    for data in [dataset_a, dataset_b, dataset_c]:
        for conf in confidences:
            assert calc_historical_var(pnl_series=data, confidence=conf) >= 0
            assert calc_cvar_expected_shortfall(pnl_series=data, confidence=conf) >= 0

def test_ordering_cvar_ge_var():
    for data in [dataset_a, dataset_b]:
        for conf in confidences:
            var = calc_historical_var(pnl_series=data, confidence=conf)
            cvar = calc_cvar_expected_shortfall(pnl_series=data, confidence=conf)
            assert cvar >= var

def test_confidence_monotonicity():
    for data in [dataset_a, dataset_b]:
        var_90 = calc_historical_var(pnl_series=data, confidence=0.9)
        var_95 = calc_historical_var(pnl_series=data, confidence=0.95)
        var_99 = calc_historical_var(pnl_series=data, confidence=0.99)
        cvar_90 = calc_cvar_expected_shortfall(pnl_series=data, confidence=0.9)
        cvar_95 = calc_cvar_expected_shortfall(pnl_series=data, confidence=0.95)
        cvar_99 = calc_cvar_expected_shortfall(pnl_series=data, confidence=0.99)
        assert var_99 >= var_95 >= var_90
        assert cvar_99 >= cvar_95 >= cvar_90

def test_all_gains_degeneracy():
    for conf in confidences:
        assert calc_historical_var(pnl_series=dataset_c, confidence=conf) == 0
        assert calc_cvar_expected_shortfall(pnl_series=dataset_c, confidence=conf) == 0

def test_scale_invariance():
    k = 3.7
    data = dataset_a
    for conf in confidences:
        var1 = calc_historical_var(pnl_series=data, confidence=conf)
        cvar1 = calc_cvar_expected_shortfall(pnl_series=data, confidence=conf)
        var2 = calc_historical_var(pnl_series=[k*x for x in data], confidence=conf)
        cvar2 = calc_cvar_expected_shortfall(pnl_series=[k*x for x in data], confidence=conf)
        assert var2 == pytest.approx(k * var1, rel=1e-12)
        assert cvar2 == pytest.approx(k * cvar1, rel=1e-12)

def test_translation_invariance():
    shift = 5.0
    data = dataset_a
    for conf in confidences:
        var1 = calc_historical_var(pnl_series=data, confidence=conf)
        cvar1 = calc_cvar_expected_shortfall(pnl_series=data, confidence=conf)
        var2 = calc_historical_var(pnl_series=[x + shift for x in data], confidence=conf)
        cvar2 = calc_cvar_expected_shortfall(pnl_series=[x + shift for x in data], confidence=conf)
        assert var2 <= var1
        assert cvar2 <= cvar1
