from datetime import datetime, timedelta
from core.persistence.sqlite_event_store import SqliteEventStore
from core.persistence.sqlite_snapshot_store import SqliteSnapshotStore
from core.v2.models import V2Event, hash_payload
from core.v2.orchestrator import V2RuntimeOrchestrator
from core.v2.snapshot_policy import EveryNSnapshotPolicy

def make_event(session_id, event_id, ts, type_, payload):
    return V2Event(
        event_id=event_id,
        session_id=session_id,
        ts=ts,
        type=type_,
        payload=payload,
        payload_hash=hash_payload(payload),
    )

def test_restart_after_crash_recovers_identical_state(tmp_path):
    db_path = str(tmp_path / "crash.db")
    snap_path = str(tmp_path / "snap.db")
    session_id = "sess1"
    event_store = SqliteEventStore(db_path)
    snap_store = SqliteSnapshotStore(snap_path)
    policy = EveryNSnapshotPolicy(2)
    orch = V2RuntimeOrchestrator(event_store, snapshot_store=snap_store, snapshot_policy=policy)
    base_ts = datetime(2025, 1, 1, 12, 0, 0)
    events = [make_event(session_id, f"evt{i}", base_ts + timedelta(seconds=i), "QUOTE_INGESTED", {"val": i}) for i in range(6)]
    for e in events:
        orch.ingest_event(e)
        orch.build_snapshot(session_id)
    state_before = orch._session_states[session_id]
    # Simulate crash: new orchestrator instance
    orch2 = V2RuntimeOrchestrator(event_store, snapshot_store=snap_store, snapshot_policy=policy)
    state_after = orch2.recover(session_id)
    assert state_before == state_after

def test_bounded_replay_does_not_replay_old_events(tmp_path):
    db_path = str(tmp_path / "bounded.db")
    snap_path = str(tmp_path / "snap2.db")
    session_id = "sess2"
    event_store = SqliteEventStore(db_path)
    snap_store = SqliteSnapshotStore(snap_path)
    policy = EveryNSnapshotPolicy(2)
    orch = V2RuntimeOrchestrator(event_store, snapshot_store=snap_store, snapshot_policy=policy)
    base_ts = datetime(2025, 1, 1, 13, 0, 0)
    events = [make_event(session_id, f"evt{i}", base_ts + timedelta(seconds=i), "QUOTE_INGESTED", {"val": i}) for i in range(5)]
    for e in events:
        orch.ingest_event(e)
        orch.build_snapshot(session_id)
    # Simulate crash
    orch2 = V2RuntimeOrchestrator(event_store, snapshot_store=snap_store, snapshot_policy=policy)
    orch2.recover(session_id)
    # Only tail events after latest snapshot should be replayed
    snap = snap_store.latest(session_id)
    tail = event_store.list_after_version(session_id, snap.version)
    assert all(e.event_id not in snap.data for e in tail)

def test_snapshot_version_monotonicity(tmp_path):
    db_path = str(tmp_path / "mono.db")
    snap_path = str(tmp_path / "snap3.db")
    session_id = "sess3"
    event_store = SqliteEventStore(db_path)
    snap_store = SqliteSnapshotStore(snap_path)
    policy = EveryNSnapshotPolicy(1)
    orch = V2RuntimeOrchestrator(event_store, snapshot_store=snap_store, snapshot_policy=policy)
    base_ts = datetime(2025, 1, 1, 14, 0, 0)
    events = [make_event(session_id, f"evt{i}", base_ts + timedelta(seconds=i), "QUOTE_INGESTED", {"val": i}) for i in range(3)]
    last_version = 0
    for e in events:
        orch.ingest_event(e)
        snap = orch.build_snapshot(session_id)
        assert snap.version > last_version
        last_version = snap.version

def test_replay_from_latest_snapshot_equivalence(tmp_path):
    db_path = str(tmp_path / "eq.db")
    snap_path = str(tmp_path / "snap4.db")
    session_id = "sess4"
    event_store = SqliteEventStore(db_path)
    snap_store = SqliteSnapshotStore(snap_path)
    policy = EveryNSnapshotPolicy(2)
    orch = V2RuntimeOrchestrator(event_store, snapshot_store=snap_store, snapshot_policy=policy)
    base_ts = datetime(2025, 1, 1, 15, 0, 0)
    events = [make_event(session_id, f"evt{i}", base_ts + timedelta(seconds=i), "QUOTE_INGESTED", {"val": i}) for i in range(6)]
    for e in events:
        orch.ingest_event(e)
        orch.build_snapshot(session_id)
    # Simulate crash
    orch2 = V2RuntimeOrchestrator(event_store, snapshot_store=snap_store, snapshot_policy=policy)
    orch2.recover(session_id)
    # Replay from genesis
    all_events = event_store.list(session_id)
    data_from_genesis = {}
    seen = set()
    for e in sorted(all_events, key=lambda e: (e.ts, e.event_id)):
        if e.event_id not in seen:
            data_from_genesis[e.event_id] = e.payload
            seen.add(e.event_id)
    # Replay from snapshot + tail
    snap = snap_store.latest(session_id)
    tail = event_store.list_after_version(session_id, snap.version)
    data_from_snap = dict(snap.data)
    for e in sorted(tail, key=lambda e: (e.ts, e.event_id)):
        if e.event_id not in data_from_snap:
            data_from_snap[e.event_id] = e.payload
    assert data_from_genesis == data_from_snap
