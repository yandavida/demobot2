from datetime import datetime
from core.persistence.sqlite_event_store import SqliteEventStore
from core.v2.models import V2Event, hash_payload

def make_event(session_id, event_id, ts, type_, payload):
    return V2Event(
        event_id=event_id,
        session_id=session_id,
        ts=ts,
        type=type_,
        payload=payload,
        payload_hash=hash_payload(payload),
    )

def test_sqlite_event_roundtrip(tmp_path):
    db_path = str(tmp_path / "events.db")
    store = SqliteEventStore(db_path)
    session_id = "sess1"
    events = [
        make_event(session_id, f"evt{i}", datetime(2025, 1, 1, 12, 0, i), "QUOTE_INGESTED", {"val": i})
        for i in range(5)
    ]
    for e in events:
        store.append(e)
    out = store.list(session_id)
    assert [e.event_id for e in out] == [e.event_id for e in events]
    # Simulate restart
    store2 = SqliteEventStore(db_path)
    out2 = store2.list(session_id)
    assert [e.event_id for e in out2] == [e.event_id for e in events]
