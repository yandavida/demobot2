import tempfile
import os
from datetime import datetime, timedelta
from core.v2.event_store_sqlite import SqliteEventStore
from core.v2.snapshot_store_sqlite import SqliteSnapshotStore
from core.v2.orchestrator import V2RuntimeOrchestrator
from core.v2.snapshot_policy import EveryNSnapshotPolicy
from core.v2.models import V2Event, hash_snapshot

def make_event(session_id, event_id, ts, payload):
    return V2Event(
        event_id=event_id,
        session_id=session_id,
        ts=ts,
        type="QUOTE_INGESTED",
        payload=payload,
        payload_hash="h",
    )

def test_crash_recovery_restart():
    fd, db_path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    try:
        session_id = "s1"
        N = 5
        # שלב 1: כתיבה ראשונית
        store = SqliteEventStore(db_path)
        snap_store = SqliteSnapshotStore(db_path)
        policy = EveryNSnapshotPolicy(N)
        orch = V2RuntimeOrchestrator(store, snap_store, policy)
        base_ts = datetime(2025, 1, 1, 12, 0, 0)
        # נכניס 10 אירועים
        for i in range(10):
            ev = make_event(session_id, f"e{i}", base_ts + timedelta(seconds=i), {"val": i})
            orch.ingest_event(ev)
        # אחרי הכנסת 10 אירועים עם cadence N=5, אמורים להישמר סנאפשוטים בגרסאות 5 ו-10
        # נכניס עוד 5 אירועים (6..10)
        for i in range(5, 10):
            ev = make_event(session_id, f"e{i}", base_ts + timedelta(seconds=i), {"val": i})
            orch.ingest_event(ev)
        # סגירה (סימולציה של קריסה)
        store.close()
        snap_store.close()
        # שלב 2: פתיחה מחדש
        store2 = SqliteEventStore(db_path)
        snap_store2 = SqliteSnapshotStore(db_path)
        orch2 = V2RuntimeOrchestrator(store2, snap_store2, policy)
        # ודא שהסנאפשוט האחרון הוא בגרסה 10
        latest = snap_store2.latest(session_id)
        assert latest is not None and latest.version == 10
        # ודא שיש סנאפשוט בגרסה 5
        snap5 = snap_store2.get_at_or_before(session_id, 5)
        assert snap5 is not None and snap5.version == 5
        # ודא שה-state מכיל את כל האירועים
        state = orch2.recover(session_id)
        assert state.version == 10
        data_keys = set(state.applied.keys())
        assert data_keys == {f"e{i}" for i in range(10)}
        # ודא שה-hash תואם ל-replay מלא (genesis)
        store3 = SqliteEventStore(db_path)
        snap_store3 = SqliteSnapshotStore(db_path)
        orch3 = V2RuntimeOrchestrator(store3, snap_store3, policy)
        state_genesis = orch3.recover(session_id)
        assert hash_snapshot(dict(state.applied)) == hash_snapshot(dict(state_genesis.applied))
    finally:
        os.remove(db_path)
