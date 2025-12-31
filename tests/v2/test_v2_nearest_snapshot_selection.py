import tempfile
import os
from datetime import datetime
from core.v2.event_store_sqlite import SqliteEventStore
from core.v2.snapshot_store_sqlite import SqliteSnapshotStore
from core.v2.models import V2Event, Snapshot
from core.v2.orchestrator import V2RuntimeOrchestrator

def make_temp_db():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    return path

def test_nearest_snapshot_selection():
    db_path = make_temp_db()
    try:
        from core.v2.models import hash_snapshot
        session_id = "A3-nearest"
        event_store = SqliteEventStore(db_path)
        snapshot_store = SqliteSnapshotStore(db_path)
        # Append e0..e2
        events1 = [
            V2Event(
                event_id=f"e{i}",
                session_id=session_id,
                ts=datetime(2025, 1, 1, 12, 0, i),
                type="QUOTE_INGESTED",
                payload={"val": i},
                payload_hash=str(i),
            )
            for i in range(3)
        ]
        for e in events1:
            event_store.append(e)
        snap1_data = {e.event_id: e.payload for e in events1}
        snap1 = Snapshot(
            session_id=session_id,
            version=3,
            state_hash=hash_snapshot(snap1_data),
            data=snap1_data,
            created_at=datetime(2025, 1, 1, 12, 0, 3),
        )
        snapshot_store.put(snap1)
        # Append e3..e4
        events2 = [
            V2Event(
                event_id=f"e{i+3}",
                session_id=session_id,
                ts=datetime(2025, 1, 1, 12, 0, i+3),
                type="QUOTE_INGESTED",
                payload={"val": i+3},
                payload_hash=str(i+3),
            )
            for i in range(2)
        ]
        for e in events2:
            event_store.append(e)
        snap2_data = {e.event_id: e.payload for e in events1 + events2}
        snap2 = Snapshot(
            session_id=session_id,
            version=5,
            state_hash=hash_snapshot(snap2_data),
            data=snap2_data,
            created_at=datetime(2025, 1, 1, 12, 0, 5),
        )
        snapshot_store.put(snap2)
        # Append tail events e5..e6
        events3 = [
            V2Event(
                event_id=f"e{i+5}",
                session_id=session_id,
                ts=datetime(2025, 1, 1, 12, 0, i+5),
                type="QUOTE_INGESTED",
                payload={"val": i+5},
                payload_hash=str(i+5),
            )
            for i in range(2)
        ]
        for e in events3:
            event_store.append(e)
        # Simulate restart
        event_store2 = SqliteEventStore(db_path)
        snapshot_store2 = SqliteSnapshotStore(db_path)
        orchestrator = V2RuntimeOrchestrator(event_store2, snapshot_store2)
        recovered = orchestrator.recover(session_id)
        # Assert latest snapshot is version=5
        latest_snap = snapshot_store2.get_latest(session_id)
        assert latest_snap.version == 5
        # Assert recovered state includes all events e0..e6
        expected_data = {e.event_id: e.payload for e in events1 + events2 + events3}
        assert recovered.applied.keys() == expected_data.keys()
        for k, v in expected_data.items():
            assert recovered.applied[k] > 0
        # Assert recovered state includes tail events (e5, e6)
        assert "e5" in recovered.applied and "e6" in recovered.applied
        # Assert recovered state includes e0..e4 as in snapshot
        for k in snap2_data:
            assert recovered.applied[k] > 0
    finally:
        os.remove(db_path)
