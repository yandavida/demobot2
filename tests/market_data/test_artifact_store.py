import pytest

from core.market_data.market_snapshot_payload_v0 import MarketSnapshotPayloadV0
import core.market_data.artifact_store as artifact_store
from core.v2.event_store_sqlite import SqliteEventStore


def make_payload() -> MarketSnapshotPayloadV0:
    return MarketSnapshotPayloadV0(
        fx_rates={"base_ccy": "USD", "quotes": {"EUR": 1.0}},
        spots={"prices": {"AAPL": 150.0}, "currency": {"AAPL": "USD"}},
        curves={"curves": {"USD": {"day_count": "ACT/365", "compounding": "continuous", "zero_rates": {"1Y": 0.02}}}},
        vols=None,
        conventions={"calendar": "US", "day_count_default": "ACT/365", "spot_lag": 2},
    )


def test_put_get_roundtrip_idempotent(tmp_path, monkeypatch):
    db_file = tmp_path / "v2.sqlite"

    # Ensure artifact_store uses our temp DB by monkeypatching the factory
    def store_factory(db_path=None):
        return SqliteEventStore(str(db_file))

    monkeypatch.setattr(artifact_store, "SqliteEventStore", store_factory)

    p = make_payload()
    msid1 = artifact_store.put_market_snapshot(p)
    assert isinstance(msid1, str) and len(msid1) == 64

    got = artifact_store.get_market_snapshot(msid1)
    assert got.model_dump() == p.model_dump()

    # Re-put identical payload is idempotent (no error)
    msid2 = artifact_store.put_market_snapshot(p)
    assert msid1 == msid2


def test_get_missing_raises_valueerror(tmp_path, monkeypatch):
    db_file = tmp_path / "v2.sqlite"

    def store_factory(db_path=None):
        return SqliteEventStore(str(db_file))

    monkeypatch.setattr(artifact_store, "SqliteEventStore", store_factory)

    with pytest.raises(ValueError) as ei:
        artifact_store.get_market_snapshot("0" * 64)
    # The ValueError should contain an ErrorEnvelope-like dict
    data = ei.value.args[0]
    assert isinstance(data, dict)
    assert data.get("code") == "market_snapshot_not_found"
