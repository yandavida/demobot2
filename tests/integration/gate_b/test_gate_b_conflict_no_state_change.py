import tempfile
import os
from datetime import datetime

import pytest

from core.v2.event_store_sqlite import SqliteEventStore
from core.v2.snapshot_store_sqlite import SqliteSnapshotStore
from core.v2.orchestrator import V2RuntimeOrchestrator
from core.v2.snapshot_policy import EveryNSnapshotPolicy
from core.v2.models import V2Event, hash_snapshot, hash_payload
from core.v2.errors import EventConflictError


def make_event(session_id, event_id, ts, payload):
    return V2Event(
        event_id=event_id,
        session_id=session_id,
        ts=ts,
        type="QUOTE_INGESTED",
        payload=payload,
        payload_hash=hash_payload(payload),
    )


def test_conflict_rejection_produces_no_state_change_across_restart():
    fd, db_path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    try:
        session_id = "R-CONF"
        event_id = "E-CONF"
        base_ts = datetime(2025, 1, 1, 10, 0, 0)

        # Large snapshot cadence to avoid implicit snapshotting during the test
        store = SqliteEventStore(db_path)
        snap_store = SqliteSnapshotStore(db_path)
        orch = V2RuntimeOrchestrator(store, snap_store, EveryNSnapshotPolicy(1000))

        # First event: apply normally
        ev1 = make_event(session_id, event_id, base_ts, {"v": 1})
        s1 = orch.ingest_event(ev1)
        assert s1.version == 1
        assert event_id in s1.applied
        assert len(store.list(session_id)) == 1

        # Second event with same event_id but different payload -> conflict at append
        # Use the store.append path which raises EventConflictError on conflicting payloads.
        ev2 = make_event(session_id, event_id, base_ts, {"v": 2})
        with pytest.raises(EventConflictError):
            store.append(ev2)

        # Ensure no side-effects were persisted by the failed/conflicting ingest
        assert len(store.list(session_id)) == 1

        # Snapshot before restart
        snap_before = snap_store.get_latest(session_id)
        hash_before = hash_snapshot(snap_before.data) if snap_before is not None else None

        # Simulate restart: close and reopen
        store.close()
        snap_store.close()

        store2 = SqliteEventStore(db_path)
        snap_store2 = SqliteSnapshotStore(db_path)
        orch2 = V2RuntimeOrchestrator(store2, snap_store2, EveryNSnapshotPolicy(1000))

        recovered = orch2.recover(session_id)
        assert recovered.version == 1
        assert event_id in recovered.applied
        assert len(store2.list(session_id)) == 1

        snap_after = snap_store2.get_latest(session_id)
        hash_after = hash_snapshot(snap_after.data) if snap_after is not None else None

        assert hash_before == hash_after

    finally:
        os.remove(db_path)
