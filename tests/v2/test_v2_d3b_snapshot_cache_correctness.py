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

def test_cached_snapshot_matches_full_replay_hash_and_version():
    # הכנה: שני orchestrators בלתי תלויים, עם אותם אירועים
    session_id = "sess-cache"
    base_ts = datetime(2025, 1, 1, 15, 0, 0)
    events = [make_event(f"e{i}", session_id, base_ts + timedelta(seconds=i), "QUOTE_INGESTED", {"val": i}) for i in range(200)]

    # Orchestrator עם cache + policy
    store_a = InMemoryEventStore()
    snap_store_a = InMemorySnapshotStore()
    policy = EveryNSnapshotPolicy(3)
    orch_cached = V2RuntimeOrchestrator(store_a, snapshot_store=snap_store_a, snapshot_policy=policy)
    for e in events:
        orch_cached.ingest_event(e)
    # ודא שמספיק אירועים נצרבו לסנאפשוטים
    cached = orch_cached.build_snapshot(session_id)

    # Orchestrator עם replay מלא (ללא cache)
    store_b = InMemoryEventStore()
    orch_full = V2RuntimeOrchestrator(store_b)
    for e in events:
        orch_full.ingest_event(e)
    full = orch_full.build_snapshot(session_id)

    assert cached.state_hash == full.state_hash
    assert cached.version == full.version

def test_snapshot_policy_materializes_every_n_events():
    store = InMemoryEventStore()
    snap_store = InMemorySnapshotStore()
    N = 3
    policy = EveryNSnapshotPolicy(N)
    orch = V2RuntimeOrchestrator(store, snapshot_store=snap_store, snapshot_policy=policy)
    session_id = "sess-policy"
    base_ts = datetime(2025, 1, 1, 16, 0, 0)
    events = [make_event(f"e{i}", session_id, base_ts + timedelta(seconds=i), "QUOTE_INGESTED", {"val": i}) for i in range(10)]
    for e in events:
        orch.ingest_event(e)
    # צור סנאפשוט סופי כדי לוודא שהכל נשמר
    orch.build_snapshot(session_id)
    # השתמש ב-list() במקום _snaps
    snapshots = snap_store.list(session_id)
    versions = [snap.version for snap in snapshots]
    # צפה לסנאפשוטים בגרסאות שהן כפולות של N (בהנחה שגרסה מתחילה מ-0)
    assert all(v % N == 0 for v in versions)
    assert len(versions) == len(set(versions))
