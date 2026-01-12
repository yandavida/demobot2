from fastapi.testclient import TestClient
from api.main import app

from core.market_data.market_snapshot_payload_v0 import (
    MarketSnapshotPayloadV0,
    FxRates,
    SpotPrices,
    Curve,
    InterestRateCurves,
    MarketConventions,
)
from core.market_data.artifact_store import put_market_snapshot, get_market_snapshot, ARTIFACT_SESSION_ID
from core.market_data.identity import market_snapshot_id
from core.v2.event_store_sqlite import SqliteEventStore
from api.v2.service_sqlite import V2ServiceSqlite

client = TestClient(app)


def make_payload(base: str = "USD", eur_rate: float = 0.9) -> MarketSnapshotPayloadV0:
    fx = FxRates(base_ccy=base, quotes={f"{base}/EUR": eur_rate, f"EUR/{base}": 1.0 / eur_rate})
    spots = SpotPrices(prices={base: 1.0, "EUR": eur_rate}, currency={base: base, "EUR": "EUR"})
    curve = Curve(day_count="ACT/365", compounding="annual", zero_rates={"1Y": 0.01})
    ircs = InterestRateCurves(curves={base: curve})
    conv = MarketConventions(calendar="TARGET", day_count_default="ACT/365", spot_lag=2)
    return MarketSnapshotPayloadV0(fx_rates=fx, spots=spots, curves=ircs, vols=None, conventions=conv)


def create_session():
    resp = client.post("/api/v2/sessions")
    assert resp.status_code == 201
    return resp.json()["session_id"]


def ingest_compute(session_id, kind, params):
    req = {"type": "COMPUTE_REQUESTED", "payload": {"kind": kind, "params": params}}
    return client.post(f"/api/v2/sessions/{session_id}/events", json=req)


def test_artifact_idempotency_and_immutability():
    p = make_payload()
    msid1 = put_market_snapshot(p)
    msid2 = put_market_snapshot(p)
    assert msid1 == msid2

    store = SqliteEventStore()
    events = [e for e in store.list(ARTIFACT_SESSION_ID) if e.event_id == msid1]
    assert len(events) == 1

    # Modify payload slightly -> new id
    p2 = make_payload(eur_rate=0.91)
    msid3 = put_market_snapshot(p2)
    assert msid3 != msid1
    events_all = {e.event_id for e in store.list(ARTIFACT_SESSION_ID)}
    assert msid1 in events_all and msid3 in events_all


def test_permutation_invariance_and_canonical_id():
    # Build two logically-equal payloads with different insertion orders
    p1 = make_payload()
    # reorder inner dicts by constructing explicit dicts in different order
    fx_quotes = {"USD/EUR": 0.9, "EUR/USD": 1.0 / 0.9}
    spots_prices = {"USD": 1.0, "EUR": 0.9}
    # reversed order
    fx_quotes_rev = {"EUR/USD": 1.0 / 0.9, "USD/EUR": 0.9}
    spots_prices_rev = {"EUR": 0.9, "USD": 1.0}

    p_a = MarketSnapshotPayloadV0(
        fx_rates=FxRates(base_ccy="USD", quotes=fx_quotes),
        spots=SpotPrices(prices=spots_prices, currency={"USD": "USD", "EUR": "EUR"}),
        curves=p1.curves,
        vols=None,
        conventions=p1.conventions,
    )
    p_b = MarketSnapshotPayloadV0(
        fx_rates=FxRates(base_ccy="USD", quotes=fx_quotes_rev),
        spots=SpotPrices(prices=spots_prices_rev, currency={"USD": "USD", "EUR": "EUR"}),
        curves=p1.curves,
        vols=None,
        conventions=p1.conventions,
    )

    id_a = market_snapshot_id(p_a)
    id_b = market_snapshot_id(p_b)
    assert id_a == id_b

    # Putting both should be idempotent (same artifact id)
    ms_a = put_market_snapshot(p_a)
    ms_b = put_market_snapshot(p_b)
    assert ms_a == ms_b


def test_restart_and_reopen_determinism():
    p = make_payload()
    msid = put_market_snapshot(p)
    fetched = get_market_snapshot(msid)
    assert fetched.model_dump() == p.model_dump()


def test_no_provider_fallback_on_compute(monkeypatch):
    # Ensure compute referencing a persisted snapshot does not call any market-data provider
    p = make_payload()
    msid = put_market_snapshot(p)

    # Patch provider methods to fail if invoked
    def _fail(*_args, **_kwargs):
        raise RuntimeError("provider should not be called during SNAPSHOT compute acceptance")

    monkeypatch.setattr("core.market_data.inmemory.InMemoryMarketDataProvider.get_price", _fail)
    monkeypatch.setattr("core.market_data.inmemory.InMemoryMarketDataProvider.get_fx_rate", _fail)
    monkeypatch.setattr("core.market_data.inmemory.InMemoryMarketDataProvider.snapshot", _fail)

    sid = create_session()
    resp = ingest_compute(sid, "SNAPSHOT", {"market_snapshot_id": msid})
    assert resp.status_code == 201


def test_service_restart_determinism(tmp_path, monkeypatch):
    # Ensure two separate V2ServiceSqlite instances backed by the same DB
    # produce the same snapshot state when recovering (restart determinism).
    db_file = tmp_path / "v2.sqlite"

    # Monkeypatch artifact_store to use the same temp DB file
    import core.market_data.artifact_store as artifact_store

    def store_factory(db_path=None):
        return SqliteEventStore(str(db_file))

    monkeypatch.setattr(artifact_store, "SqliteEventStore", store_factory)

    # First service instance: create session, persist snapshot, ingest compute
    svc1 = V2ServiceSqlite(db_path=str(db_file))
    sid = svc1.create_session()
    p = make_payload()
    msid = put_market_snapshot(p)

    # Ingest compute via service instance 1
    state_before = svc1.ingest_event(sid, event_id=None, ts=None, type="COMPUTE_REQUESTED", payload={"kind": "SNAPSHOT", "params": {"market_snapshot_id": msid}})
    snap1 = svc1.get_snapshot(sid)
    svc1.close()

    # New service instance simulating a restart
    svc2 = V2ServiceSqlite(db_path=str(db_file))
    # Ensure session visible to restarted service
    assert svc2.get_session(sid) is not None
    snap2 = svc2.get_snapshot(sid)

    # Snapshot state must match across restart
    assert snap1.state_hash == snap2.state_hash
    assert snap1.data == snap2.data

    # Ingesting the same compute on restarted service should be accepted
    state_after = svc2.ingest_event(sid, event_id=None, ts=None, type="COMPUTE_REQUESTED", payload={"kind": "SNAPSHOT", "params": {"market_snapshot_id": msid}})
    assert isinstance(state_before[0], int) and isinstance(state_before[1], bool)
    assert isinstance(state_after[0], int) and isinstance(state_after[1], bool)
    svc2.close()


def test_snapshot_compute_does_not_use_runtime_clock():
    """Scoped static scan for forbidden runtime clock usage in Gate M modules.

    This is a scoped fallback test: it scans `core/market_data/` for occurrences
    of `.now(` or `utcnow(` which would indicate runtime clock usage that
    could introduce nondeterminism at Gate M. This test intentionally scans
    only the market-data boundary modules (Gate M) to avoid false positives
    from general service timestamping in `api.v2.service_sqlite` or
    `core.v2.orchestrator` which legitimately use clocks for metadata.
    """
    import pathlib

    repo_root = pathlib.Path(__file__).resolve().parents[3]
    # Scope the static scan to the files directly involved in Gate M acceptance
    targets = [
        repo_root / "core" / "market_data" / "artifact_store.py",
        repo_root / "core" / "market_data" / "identity.py",
        repo_root / "core" / "market_data" / "validate_requirements.py",
    ]
    forbidden_patterns = [".now(", "utcnow(", "datetime.utcnow", "datetime.now"]
    matches = []
    for path in targets:
        if not path.exists():
            continue
        txt = path.read_text(encoding="utf-8")
        for pat in forbidden_patterns:
            if pat in txt:
                matches.append(f"{path.relative_to(repo_root)}: contains '{pat}'")
    assert matches == [], "Found runtime clock usage in Gate M acceptance modules:\n" + "\n".join(matches)
