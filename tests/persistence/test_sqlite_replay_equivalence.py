from datetime import datetime
from core.persistence.sqlite_event_store import SqliteEventStore
from core.v2.event_store import InMemoryEventStore
from core.v2.models import V2Event, hash_payload
from core.v2.replay import replay_events

def make_event(session_id, event_id, ts, type_, payload):
    return V2Event(
        event_id=event_id,
        session_id=session_id,
        ts=ts,
        type=type_,
        payload=payload,
        payload_hash=hash_payload(payload),
    )

def test_sqlite_replay_equivalence(tmp_path):
    db_path = str(tmp_path / "replay.db")
    session_id = "sess1"
    mem_store = InMemoryEventStore()
    sqlite_store = SqliteEventStore(db_path)
    events = [
        make_event(session_id, f"evt{i}", datetime(2025, 1, 1, 12, 0, i), "QUOTE_INGESTED", {"val": i})
        for i in range(10)
    ]
    for e in events:
        mem_store.append(e)
        sqlite_store.append(e)
    mem_out = replay_events(mem_store.list(session_id))
    sqlite_out = replay_events(sqlite_store.list(session_id))
    assert mem_out == sqlite_out
    # Compare hashes for determinism
    assert [e.payload_hash for e in mem_store.list(session_id)] == [e.payload_hash for e in sqlite_store.list(session_id)]
