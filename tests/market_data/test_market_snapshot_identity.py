from core.market_data.market_snapshot_payload_v0 import MarketSnapshotPayloadV0
from core.market_data.identity import market_snapshot_id


def make_payload(base: str = "USD") -> MarketSnapshotPayloadV0:
    return MarketSnapshotPayloadV0(
        schema_version="0",
        fx_rates={f"{base}/EUR": 0.9, f"EUR/{base}": 1.0 / 0.9},
        spots={base: 1.0, "EUR": 0.9},
        interest_rate_curves={base: {"1Y": 0.01}},
        vols=None,
        market_conventions={"base_currency": base},
    )


def test_same_payload_same_id():
    p1 = make_payload()
    p2 = make_payload()
    assert market_snapshot_id(p1) == market_snapshot_id(p2)


def test_different_payload_different_id():
    p1 = make_payload()
    p2 = make_payload(base="GBP")
    assert market_snapshot_id(p1) != market_snapshot_id(p2)
