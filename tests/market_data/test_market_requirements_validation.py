from core.market_data.market_snapshot_payload_v0 import (
    MarketSnapshotPayloadV0,
    FxRates,
    SpotPrices,
    Curve,
    InterestRateCurves,
    MarketConventions,
)
from core.commands.compute_request_command import ComputeRequestPayload
from core.market_data.validate_requirements import validate_market_requirements


def make_payload(base: str = "USD") -> MarketSnapshotPayloadV0:
    fx = FxRates(base_ccy=base, quotes={f"{base}/EUR": 0.9, f"EUR/{base}": 1.0 / 0.9})
    spots = SpotPrices(prices={base: 1.0, "EUR": 0.9}, currency={base: base, "EUR": "EUR"})
    curve = Curve(day_count="ACT/365", compounding="annual", zero_rates={"1Y": 0.01})
    ircs = InterestRateCurves(curves={base: curve})
    conv = MarketConventions(calendar="TARGET", day_count_default="ACT/365", spot_lag=2)
    return MarketSnapshotPayloadV0(fx_rates=fx, spots=spots, curves=ircs, vols=None, conventions=conv)


def test_missing_symbol_returns_semantic_error():
    snap = make_payload()
    req = ComputeRequestPayload(kind="SNAPSHOT", params={"symbols": ["FOO"]})
    err = validate_market_requirements(req, snap)
    assert err is not None
    assert err.code == "UNKNOWN_SYMBOL_IN_SNAPSHOT"


def test_missing_spot_currency_returns_semantic_error():
    snap = make_payload()
    # remove currency mapping for USD to simulate missing mapping
    snap.spots.currency.pop("USD", None)
    req = ComputeRequestPayload(kind="SNAPSHOT", params={"symbols": ["USD"]})
    err = validate_market_requirements(req, snap)
    assert err is not None
    assert err.code == "MISSING_SPOT_CURRENCY"


def test_missing_fx_pair_returns_semantic_error():
    snap = make_payload(base="USD")
    # remove USD/EUR to force missing pair when base_ccy differs
    snap.fx_rates.quotes.pop("EUR/USD", None)
    # request base_ccy USD but symbol EUR (EUR currency -> EUR/USD required)
    req = ComputeRequestPayload(kind="SNAPSHOT", params={"symbols": ["EUR"], "base_ccy": "USD"})
    err = validate_market_requirements(req, snap)
    assert err is not None
    assert err.code == "MISSING_FX_PAIR"


def test_missing_curve_returns_semantic_error():
    snap = make_payload()
    req = ComputeRequestPayload(kind="SNAPSHOT", params={"required_curves": ["GBP"]})
    err = validate_market_requirements(req, snap)
    assert err is not None
    assert err.code == "MISSING_CURVE"


def test_missing_tenor_returns_semantic_error():
    snap = make_payload()
    req = ComputeRequestPayload(kind="SNAPSHOT", params={"tenors": {"USD": ["2Y"]}})
    err = validate_market_requirements(req, snap)
    assert err is not None
    assert err.code == "MISSING_TENOR"
