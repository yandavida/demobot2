from core.market_data.market_snapshot_payload_v0 import (
    MarketSnapshotPayloadV0,
    FxRates,
    SpotPrices,
    Curve,
    InterestRateCurves,
    MarketConventions,
)
from core.market_data.identity import market_snapshot_id


def make_payload(base: str = "USD") -> MarketSnapshotPayloadV0:
    fx = FxRates(base_ccy=base, quotes={f"{base}/EUR": 0.9, f"EUR/{base}": 1.0 / 0.9})
    spots = SpotPrices(prices={base: 1.0, "EUR": 0.9}, currency={base: base, "EUR": "EUR"})
    curve = Curve(day_count="ACT/365", compounding="annual", zero_rates={"1Y": 0.01})
    ircs = InterestRateCurves(curves={base: curve})
    conv = MarketConventions(calendar="TARGET", day_count_default="ACT/365", spot_lag=2)
    return MarketSnapshotPayloadV0(fx_rates=fx, spots=spots, curves=ircs, vols=None, conventions=conv)


def test_same_payload_same_id():
    p1 = make_payload()
    p2 = make_payload()
    assert market_snapshot_id(p1) == market_snapshot_id(p2)


def test_different_payload_different_id():
    p1 = make_payload()
    p2 = make_payload(base="GBP")
    assert market_snapshot_id(p1) != market_snapshot_id(p2)
