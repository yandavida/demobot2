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

def test_replay_equivalence_genesis_vs_snapshot():
    db_path = make_temp_db()
    try:
        from core.v2.models import hash_snapshot
        session_id = "A4-equivalence"
        # Build deterministic event stream
        events = [
            V2Event(
                event_id=f"e{i}",
                session_id=session_id,
                ts=datetime(2025, 1, 1, 12, 0, i),
                type="QUOTE_INGESTED",
                payload={"val": i},
                payload_hash=str(i),
            )
            for i in range(5)
        ]
        # Path A: replay from genesis
        event_store = SqliteEventStore(db_path)
        snapshot_store = SqliteSnapshotStore(db_path)
        for e in events:
            event_store.append(e)
        orchestrator = V2RuntimeOrchestrator(event_store, snapshot_store)
        state_A = orchestrator.recover(session_id)
        state_hash_A = hash_snapshot({e.event_id: e.payload for e in events})
        # Create snapshot(s)
        snap_data = {e.event_id: e.payload for e in events}
        snap = Snapshot(
            session_id=session_id,
            version=5,
            state_hash=hash_snapshot(snap_data),
            data=snap_data,
            created_at=datetime(2025, 1, 1, 12, 0, 5),
        )
        snapshot_store.put(snap)
        # Path B: restart and replay from nearest snapshot
        event_store2 = SqliteEventStore(db_path)
        snapshot_store2 = SqliteSnapshotStore(db_path)
        orchestrator2 = V2RuntimeOrchestrator(event_store2, snapshot_store2)
        state_B = orchestrator2.recover(session_id)
        # הפק את ה-data בפועל מתוך state_B (בהנחה שיש לו data או שניתן לבנות אותה מ-applied)
        # נבנה dict event_id→payload לפי סדר האירועים
        # נניח שהסדר ב-applied תואם את הסדר הדטרמיניסטי
        recovered_event_ids = list(state_B.applied.keys())
        # שלוף את כל האירועים מה-store כדי לשחזר את ה-payloads
        all_events = event_store2.list(session_id)
        event_map = {e.event_id: e.payload for e in all_events}
        recovered_data = {eid: event_map[eid] for eid in recovered_event_ids}
        # השווה hash דטרמיניסטי של ה-data
        assert state_hash_A == hash_snapshot(recovered_data)
    finally:
        os.remove(db_path)
