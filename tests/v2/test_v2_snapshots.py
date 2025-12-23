from core.v2.models import V2Event, hash_payload
from core.v2.event_store import InMemoryEventStore
from core.v2.orchestrator import V2RuntimeOrchestrator
from core.v2.snapshot_store import InMemorySnapshotStore
from core.v2.snapshot_policy import EveryNSnapshotPolicy
from core.v2.replay import replay_applied, replay_from_snapshot
from datetime import datetime, timedelta

# Helper to create events with fixed ids and timestamps
def make_event(event_id, session_id, ts, type, payload):
    return V2Event(
        event_id=event_id,
        session_id=session_id,
        ts=ts,
        type=type,
        payload=payload,
        payload_hash=hash_payload(payload),
    )

def test_applied_versions_and_mapping():
    store = InMemoryEventStore()
    orch = V2RuntimeOrchestrator(store)
    session_id = "sessA"
    base_ts = datetime(2025, 1, 1, 10, 0, 0)
    events = [make_event(f"e{i}", session_id, base_ts + timedelta(seconds=i), "QUOTE_INGESTED", {"val": i}) for i in range(5)]
    for e in events:
        orch.ingest_event(e)
    state = orch._session_states[session_id]
    # Version should be 5, mapping correct
    assert state.version == 5
    for i, e in enumerate(events):
        assert state.applied[e.event_id] == i + 1

def test_idempotency_preserves_mapping():
    store = InMemoryEventStore()
    orch = V2RuntimeOrchestrator(store)
    session_id = "sessB"
    ts = datetime(2025, 1, 1, 11, 0, 0)
    e = make_event("evt1", session_id, ts, "QUOTE_INGESTED", {"foo": 1})
    orch.ingest_event(e)
    state1 = orch._session_states[session_id]
    orch.ingest_event(e)  # duplicate
    state2 = orch._session_states[session_id]
    assert state2.version == state1.version
    assert state2.applied == state1.applied

def test_replay_from_snapshot_equivalence():
    store = InMemoryEventStore()
    snap_store = InMemorySnapshotStore()
    policy = EveryNSnapshotPolicy(3)
    orch = V2RuntimeOrchestrator(store, snapshot_store=snap_store, snapshot_policy=policy)
    session_id = "sessC"
    base_ts = datetime(2025, 1, 1, 12, 0, 0)
    events = [make_event(f"e{i}", session_id, base_ts + timedelta(seconds=i), "QUOTE_INGESTED", {"val": i}) for i in range(6)]
    for e in events:
        orch.ingest_event(e)
        orch.build_snapshot(session_id)  # force snapshot policy
    # Get latest snapshot
    latest = snap_store.latest(session_id)
    assert latest is not None
    # Get applied log
    applied_log = orch._applied_log[session_id]
    # Find tail after snapshot
    tail = [ae for ae in applied_log if ae.state_version > latest.version]
    # Replay from snapshot + tail
    replayed = replay_from_snapshot(latest, tail)
    # Replay from genesis
    full = replay_applied(applied_log)
    assert replayed == full

def test_latest_snapshot_correctness():
    store = InMemoryEventStore()
    snap_store = InMemorySnapshotStore()
    policy = EveryNSnapshotPolicy(2)
    orch = V2RuntimeOrchestrator(store, snapshot_store=snap_store, snapshot_policy=policy)
    session_id = "sessD"
    base_ts = datetime(2025, 1, 1, 13, 0, 0)
    events = [make_event(f"e{i}", session_id, base_ts + timedelta(seconds=i), "QUOTE_INGESTED", {"val": i}) for i in range(4)]
    for e in events:
        orch.ingest_event(e)
        orch.build_snapshot(session_id)
    latest = snap_store.latest(session_id)
    assert latest is not None
    assert latest.version == 4
    # Data must match replay_applied
    applied_log = orch._applied_log[session_id]
    assert latest.data == replay_applied(applied_log)

def test_bounded_rebuild_path():
    store = InMemoryEventStore()
    snap_store = InMemorySnapshotStore()
    policy = EveryNSnapshotPolicy(2)
    orch = V2RuntimeOrchestrator(store, snapshot_store=snap_store, snapshot_policy=policy)
    session_id = "sessE"
    base_ts = datetime(2025, 1, 1, 14, 0, 0)
    events = [make_event(f"e{i}", session_id, base_ts + timedelta(seconds=i), "QUOTE_INGESTED", {"val": i}) for i in range(6)]
    for e in events:
        orch.ingest_event(e)
        orch.build_snapshot(session_id)
    # Get latest snapshot
    latest = snap_store.latest(session_id)
    assert latest is not None
    # Get applied log
    applied_log = orch._applied_log[session_id]
    # Find tail after snapshot
    tail = [ae for ae in applied_log if ae.state_version > latest.version]
    # Bounded replay must use only tail (not all events)
    assert len(tail) < len(applied_log)
    # Replay from snapshot + tail must match full replay
    replayed = replay_from_snapshot(latest, tail)
    full = replay_applied(applied_log)
    assert replayed == full
