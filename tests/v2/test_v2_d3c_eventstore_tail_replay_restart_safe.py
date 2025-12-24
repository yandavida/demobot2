from datetime import datetime, timedelta
from core.v2.models import V2Event, hash_payload
from core.v2.event_store import InMemoryEventStore
from core.v2.orchestrator import V2RuntimeOrchestrator
from core.v2.snapshot_store import InMemorySnapshotStore
from core.v2.snapshot_policy import EveryNSnapshotPolicy

def make_event(event_id, session_id, ts, type, payload):
    return V2Event(
        event_id=event_id,
        session_id=session_id,
        ts=ts,
        type=type,
        payload=payload,
        payload_hash=hash_payload(payload),
    )

def test_cached_snapshot_equals_full_replay():
    session_id = "sess-d3c"
    base_ts = datetime(2025, 1, 1, 17, 0, 0)
    events = [make_event(f"e{i}", session_id, base_ts + timedelta(seconds=i), "QUOTE_INGESTED", {"val": i}) for i in range(200)]
    store = InMemoryEventStore()
    snap_store = InMemorySnapshotStore()
    policy = EveryNSnapshotPolicy(5)
    orch = V2RuntimeOrchestrator(store, snapshot_store=snap_store, snapshot_policy=policy)
    for e in events:
        orch.ingest_event(e)
    cached = orch.build_snapshot(session_id)
    orch_full = V2RuntimeOrchestrator(store)
    full = orch_full.build_snapshot(session_id)
    assert cached.state_hash == full.state_hash
    assert cached.version == full.version

def test_restart_safe_snapshot_building():
    session_id = "sess-d3c-restart"
    base_ts = datetime(2025, 1, 1, 18, 0, 0)
    events = [make_event(f"e{i}", session_id, base_ts + timedelta(seconds=i), "QUOTE_INGESTED", {"val": i}) for i in range(100)]
    store = InMemoryEventStore()
    snap_store = InMemorySnapshotStore()
    policy = EveryNSnapshotPolicy(7)
    orch1 = V2RuntimeOrchestrator(store, snapshot_store=snap_store, snapshot_policy=policy)
    for e in events:
        orch1.ingest_event(e)
    snap1 = orch1.build_snapshot(session_id)
    # סימולציית restart: יוצר orchestrator חדש עם אותם חנויות
    orch2 = V2RuntimeOrchestrator(store, snapshot_store=snap_store, snapshot_policy=policy)
    snap2 = orch2.build_snapshot(session_id)
    # השוואה מול replay מלא
    orch_full = V2RuntimeOrchestrator(store)
    snap_full = orch_full.build_snapshot(session_id)
    assert snap2.state_hash == snap_full.state_hash
    assert snap2.version == snap_full.version
    assert snap1.state_hash == snap2.state_hash
    assert snap1.version == snap2.version
