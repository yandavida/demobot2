import importlib
import math


def test_policy_declares_canonical_units_for_vega_theta():
    np = importlib.import_module("core.numeric_policy")
    assert np.VEGA_UNIT == "per_1pct_iv"
    assert np.THETA_UNIT == "per_calendar_day"


def test_units_canonicalization_scales_raw_vega_to_per_1pct_iv():
    bs = importlib.import_module("core.pricing.bs")
    units = importlib.import_module("core.pricing.units")

    # stable inputs
    spot = 100.0
    strike = 100.0
    t = 1.0
    rate = 0.0
    div = 0.0
    vol = 0.20
    opt_type = "C"

    raw = bs.bs_greeks(opt_type, spot, strike, rate, div, vol, t)
    canon = units.to_canonical_greeks(raw)

    # canonical vega should equal raw vega divided by 100.0
    assert math.isclose(canon["vega"], raw["vega"] / 100.0, rel_tol=1e-12)


def test_units_canonicalization_scales_raw_theta_to_per_day():
    bs = importlib.import_module("core.pricing.bs")
    units = importlib.import_module("core.pricing.units")

    spot = 100.0
    strike = 100.0
    t = 1.0
    rate = 0.0
    div = 0.0
    vol = 0.20
    opt_type = "C"

    raw = bs.bs_greeks(opt_type, spot, strike, rate, div, vol, t)
    canon = units.to_canonical_greeks(raw)

    # canonical theta should equal raw theta divided by 365.0
    assert math.isclose(canon["theta"], raw["theta"] / 365.0, rel_tol=1e-12)


def test_portfolio_greeks_aggregation_respects_canonical_units():
    greeks_mod = importlib.import_module("core.greeks")
    units = importlib.import_module("core.pricing.units")
    bs = importlib.import_module("core.pricing.bs")

    # Build two identical raw greeks dicts, canonicalize them, then aggregate.
    spot = 100.0
    strike = 100.0
    t = 1.0
    rate = 0.0
    div = 0.0
    vol = 0.20
    opt_type = "C"

    raw = bs.bs_greeks(opt_type, spot, strike, rate, div, vol, t)
    canon1 = units.to_canonical_greeks(raw)
    canon2 = units.to_canonical_greeks(raw)

    aggregated = greeks_mod.aggregate_greeks([canon1, canon2])

    # Aggregation should be linear: aggregated == 2 * single
    for k in ("vega", "theta", "delta", "gamma", "rho"):
        assert math.isclose(aggregated[k], 2.0 * canon1[k], rel_tol=1e-12)
