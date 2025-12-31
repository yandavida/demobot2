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

def test_reopen_idempotency():
    fd, db_path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    try:
        session_id = "s2"
        N = 5
        store = SqliteEventStore(db_path)
        snap_store = SqliteSnapshotStore(db_path)
        policy = EveryNSnapshotPolicy(N)
        orch = V2RuntimeOrchestrator(store, snap_store, policy)
        base_ts = datetime(2025, 1, 1, 13, 0, 0)
        for i in range(10):
            ev = make_event(session_id, f"e{i}", base_ts + timedelta(seconds=i), {"val": i})
            orch.ingest_event(ev)
        store.close()
        snap_store.close()
        # פתיחה מחדש והרצה פעמיים
        hashes = []
        for _ in range(2):
            store2 = SqliteEventStore(db_path)
            snap_store2 = SqliteSnapshotStore(db_path)
            # יצירת policy חדש בכל איטרציה
            orch2 = V2RuntimeOrchestrator(store2, snap_store2, EveryNSnapshotPolicy(N))
            state = orch2.recover(session_id)
            hashes.append(hash_snapshot(dict(state.applied)))
            store2.close()
            snap_store2.close()
        assert hashes[0] == hashes[1]
    finally:
        os.remove(db_path)
