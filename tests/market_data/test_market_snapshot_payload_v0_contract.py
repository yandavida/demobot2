from core.market_data.market_snapshot_payload_v0 import (
    MarketSnapshotPayloadV0,
    FxRates,
    SpotPrices,
    InterestRateCurves,
    Curve,
    VolSurfaces,
    VolSurface,
    MarketConventions,
)
from core.market_data.validate_market_snapshot_v0 import validate_market_snapshot_v0


def _example_snapshot():
    fx = FxRates(base_ccy="USD", quotes={"USD/USD": 1.0, "USD/ILS": 3.72, "ILS/USD": 1 / 3.72})
    spots = SpotPrices(prices={"AAPL": 150.0}, currency={"AAPL": "USD"})
    curve = Curve(day_count="ACT/365", compounding="annual", zero_rates={"1M": 0.01, "3M": 0.012, "1Y": 0.02})
    curves = InterestRateCurves(curves={"USD": curve})
    vols = VolSurfaces(surfaces={"AAPL": VolSurface(type="flat", data={"vol": 0.25})})
    conv = MarketConventions(calendar="NONE", day_count_default="ACT/365", spot_lag=2)
    return MarketSnapshotPayloadV0(fx_rates=fx, spots=spots, curves=curves, vols=vols, conventions=conv)


def test_roundtrip_json_serialization():
    s = _example_snapshot()
    j = s.model_dump_json()
    s2 = MarketSnapshotPayloadV0.model_validate_json(j)
    assert s.model_dump() == s2.model_dump()


def test_fx_symmetry_missing_inverse():
    s = _example_snapshot()
    # remove inverse
    del s.fx_rates.quotes["ILS/USD"]
    err = validate_market_snapshot_v0(s)
    assert err is not None
    assert err.code == "fx_missing_inverse"


def test_fx_base_must_be_one():
    s = _example_snapshot()
    s.fx_rates.quotes["USD/USD"] = 1.0001
    err = validate_market_snapshot_v0(s)
    assert err is not None
    assert err.code == "fx_base_not_one"


def test_spot_requires_currency_mapping():
    s = _example_snapshot()
    s.spots.prices["GOOG"] = 2000.0
    # no currency mapping for GOOG
    err = validate_market_snapshot_v0(s)
    assert err is not None
    assert err.code == "spot_missing_currency"


def test_curve_invalid_tenor():
    s = _example_snapshot()
    s.curves.curves["USD"].zero_rates["13Q"] = 0.05
    err = validate_market_snapshot_v0(s)
    assert err is not None
    assert err.code == "curve_invalid_tenor"


def test_vols_accept_none_and_flat_and_reject_nonflat():
    s = _example_snapshot()
    # vols present and flat OK
    err = validate_market_snapshot_v0(s)
    assert err is None

    # None is allowed
    s2 = _example_snapshot()
    s2.vols = None
    err2 = validate_market_snapshot_v0(s2)
    assert err2 is None

    # non-flat rejected
    s3 = _example_snapshot()
    s3.vols.surfaces["AAPL"].type = "smile"
    err3 = validate_market_snapshot_v0(s3)
    assert err3 is not None
    assert err3.code == "volsurface_type_not_allowed"
