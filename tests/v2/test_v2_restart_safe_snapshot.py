import tempfile
import os
from datetime import datetime
from core.v2.snapshot_store_sqlite import SqliteSnapshotStore
from core.v2.event_store_sqlite import SqliteEventStore
from core.v2.models import V2Event, Snapshot
from core.v2.event_ordering import stable_sort_events

def make_temp_db():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    return path

def test_restart_safe_snapshot_state_hash_and_version():
    db_path = make_temp_db()
    try:
        event_store = SqliteEventStore(db_path)
        snapshot_store = SqliteSnapshotStore(db_path)
        session_id = "sessA4-1"
        events = [
            V2Event(
                event_id=f"evt{i}",
                session_id=session_id,
                ts=datetime(2025, 1, 1, 12, 0, i),
                type="QUOTE_INGESTED",
                payload={"val": i},
                payload_hash=str(i),
            )
            for i in range(5)
        ]
        for e in events:
            event_store.append(e)
        # Create snapshot
        snap1 = Snapshot(
            session_id=session_id,
            version=5,
            state_hash="h1",
            data={e.event_id: e.payload for e in events},
            created_at=datetime(2025, 1, 1, 12, 0, 5),
        )
        snapshot_store.put(snap1)
        # Simulate restart: re-instantiate stores
        event_store2 = SqliteEventStore(db_path)
        snapshot_store2 = SqliteSnapshotStore(db_path)
        snap2 = snapshot_store2.get_latest(session_id)
        assert snap2 is not None
        assert snap2.state_hash == snap1.state_hash
        assert snap2.version == snap1.version
    finally:
        os.remove(db_path)

def test_restart_safe_snapshot_reorder_idempotent():
    db_path = make_temp_db()
    try:
        event_store = SqliteEventStore(db_path)
        snapshot_store = SqliteSnapshotStore(db_path)
        session_id1 = "sessA4-2a"
        session_id2 = "sessA4-2b"
        # Same events, different order
        events1 = [
            V2Event(event_id="a", session_id=session_id1, ts=datetime(2025,1,1,12,0,0), type="QUOTE_INGESTED", payload={"v":1}, payload_hash="1"),
            V2Event(event_id="b", session_id=session_id1, ts=datetime(2025,1,1,12,0,0), type="QUOTE_INGESTED", payload={"v":2}, payload_hash="2"),
        ]
        events2 = list(reversed(events1))
        for e in events1:
            event_store.append(e)
        for e in events2:
            event_store.append(e)
        snap1 = Snapshot(
            session_id=session_id1,
            version=2,
            state_hash="h2",
            data={e.event_id: e.payload for e in stable_sort_events(events1)},
            created_at=datetime(2025,1,1,12,0,1),
        )
        snapshot_store.put(snap1)
        # Simulate restart
        event_store2 = SqliteEventStore(db_path)
        snapshot_store2 = SqliteSnapshotStore(db_path)
        snap2 = snapshot_store2.get_latest(session_id1)
        assert snap2 is not None
        assert snap2.state_hash == snap1.state_hash
        assert snap2.version == snap1.version
    finally:
        os.remove(db_path)

def test_restart_safe_snapshot_duplicate_idempotent():
    db_path = make_temp_db()
    try:
        event_store = SqliteEventStore(db_path)
        snapshot_store = SqliteSnapshotStore(db_path)
        session_id = "sessA4-3"
        e = V2Event(event_id="dup", session_id=session_id, ts=datetime(2025,1,1,12,0,0), type="QUOTE_INGESTED", payload={"v":1}, payload_hash="1")
        event_store.append(e)
        event_store.append(e)  # duplicate
        snap = Snapshot(
            session_id=session_id,
            version=1,
            state_hash="h3",
            data={e.event_id: e.payload},
            created_at=datetime(2025,1,1,12,0,1),
        )
        snapshot_store.put(snap)
        # Simulate restart
        event_store2 = SqliteEventStore(db_path)
        snapshot_store2 = SqliteSnapshotStore(db_path)
        snap2 = snapshot_store2.get_latest(session_id)
        assert snap2 is not None
        assert snap2.state_hash == snap.state_hash
        assert snap2.version == snap.version
    finally:
        os.remove(db_path)
