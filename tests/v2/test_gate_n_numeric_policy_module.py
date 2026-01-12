import importlib


def test_numeric_policy_imports_cleanly():
    np = importlib.import_module("core.numeric_policy")
    assert hasattr(np, "RATE_UNIT")
    assert hasattr(np, "DEFAULT_TOLERANCES")
    assert hasattr(np, "MetricClass")


def test_default_tolerances_cover_all_metric_classes():
    np = importlib.import_module("core.numeric_policy")
    for mc in np.MetricClass:
        assert mc in np.DEFAULT_TOLERANCES


def test_default_tolerances_are_placeholders():
    np = importlib.import_module("core.numeric_policy")
    for tol in np.DEFAULT_TOLERANCES.values():
        assert tol.abs is None and tol.rel is None


def test_units_constants_locked_for_vega_theta():
    np = importlib.import_module("core.numeric_policy")
    assert np.VEGA_UNIT == "per_1pct_iv"
    assert np.THETA_UNIT == "per_calendar_day"
