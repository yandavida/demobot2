import tempfile
import os
from datetime import datetime

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


def test_retry_idempotency_across_restarts():
    fd, db_path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    try:
        session_id = "R1"
        command_id = "CMD-X"
        base_ts = datetime(2025, 1, 1, 10, 0, 0)

        # Use a very large snapshot cadence to avoid implicit snapshotting during the test
        store = SqliteEventStore(db_path)
        snap_store = SqliteSnapshotStore(db_path)
        orch = V2RuntimeOrchestrator(store, snap_store, EveryNSnapshotPolicy(1000))

        # Submit command once
        ev = make_event(session_id, command_id, base_ts, {"v": 1})
        s1 = orch.ingest_event(ev)
        assert s1.version == 1
        assert command_id in s1.applied
        assert len(store.list(session_id)) == 1

        # Re-submit same command: must be idempotent (no new event, no state change)
        s2 = orch.ingest_event(ev)
        assert s2.version == 1
        assert command_id in s2.applied
        assert len(store.list(session_id)) == 1

        # Record snapshot/hash before restart (may be None)
        snap_before = snap_store.get_latest(session_id)
        hash_before = hash_snapshot(snap_before.data) if snap_before is not None else None

        # Simulate restart: close and reopen stores/orchestrator
        store.close()
        snap_store.close()

        store2 = SqliteEventStore(db_path)
        snap_store2 = SqliteSnapshotStore(db_path)
        orch2 = V2RuntimeOrchestrator(store2, snap_store2, EveryNSnapshotPolicy(1000))

        recovered = orch2.recover(session_id)
        assert recovered.version == 1
        assert command_id in recovered.applied
        assert len(store2.list(session_id)) == 1

        # Re-submit again after restart: still idempotent
        s3 = orch2.ingest_event(ev)
        assert s3.version == 1
        assert command_id in s3.applied
        assert len(store2.list(session_id)) == 1

        snap_after = snap_store2.get_latest(session_id)
        hash_after = hash_snapshot(snap_after.data) if snap_after is not None else None

        assert hash_before == hash_after

    finally:
        os.remove(db_path)
