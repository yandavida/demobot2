import tempfile
import os
from datetime import datetime

from core.v2.event_store_sqlite import SqliteEventStore
from core.v2.snapshot_store_sqlite import SqliteSnapshotStore
from core.v2.orchestrator import V2RuntimeOrchestrator
from core.v2.snapshot_policy import EveryNSnapshotPolicy
from core.v2.models import V2Event


def make_event(session_id, event_id, ts, payload):
    return V2Event(
        event_id=event_id,
        session_id=session_id,
        ts=ts,
        type="QUOTE_INGESTED",
        payload=payload,
        payload_hash="h",
    )


def test_persist_reopen_seen_idempotency():
    fd, db_path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    try:
        session_id = "S1"
        store = SqliteEventStore(db_path)
        snap_store = SqliteSnapshotStore(db_path)
        orch = V2RuntimeOrchestrator(store, snap_store, EveryNSnapshotPolicy(10))
        base_ts = datetime(2025, 1, 1, 12, 0, 0)

        # Initial persist
        ev = make_event(session_id, "e1", base_ts, {"val": 1})
        state1 = orch.ingest_event(ev)
        assert state1.version == 1
        assert "e1" in state1.applied
        count_after_first = len(store.list(session_id))
        assert count_after_first == 1

        # Close (simulate shutdown) and reopen (simulate restart)
        store.close()
        snap_store.close()

        store2 = SqliteEventStore(db_path)
        snap_store2 = SqliteSnapshotStore(db_path)
        orch2 = V2RuntimeOrchestrator(store2, snap_store2, EveryNSnapshotPolicy(10))

        recovered = orch2.recover(session_id)
        assert recovered.version == 1
        assert "e1" in recovered.applied
        assert len(store2.list(session_id)) == 1

        # Re-submit identical event after restart: must be seen (idempotent) and not duplicated
        state_after_resubmit = orch2.ingest_event(ev)
        assert state_after_resubmit.version == 1
        assert "e1" in state_after_resubmit.applied
        assert len(store2.list(session_id)) == 1

    finally:
        os.remove(db_path)
