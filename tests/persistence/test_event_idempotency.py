import pytest
from datetime import datetime
from core.v2.models import V2Event
from core.v2.event_store_sqlite import SqliteEventStore
from core.v2.errors import EventConflictError
from core.v2.sqlite_schema import ensure_schema

def make_event(session_id: str, event_id: str, payload: dict, payload_hash: str, type_: str = "QUOTE_INGESTED") -> V2Event:
    return V2Event(
        event_id=event_id,
        session_id=session_id,
        ts=datetime.utcnow(),
        type=type_,
        payload=payload,
        payload_hash=payload_hash,
    )

def test_event_idempotency_and_conflict(tmp_path):
    db_path = tmp_path / "test.sqlite"
    store = SqliteEventStore(str(db_path))
    # Ensure schema
    with store._connect() as conn:
        ensure_schema(conn)

    session_id = "s1"
    event_id = "e1"
    payload = {"foo": 1}
    payload_hash = "hash1"
    event = make_event(session_id, event_id, payload, payload_hash, type_="QUOTE_INGESTED")


    # First insert: should apply
    result1 = store.append(event)
    assert result1 is True

    # Second insert: idempotent, should not apply
    result2 = store.append(event)
    assert result2 is False

    db_path = tmp_path / "test.sqlite"
    store = SqliteEventStore(str(db_path))
    with store._connect() as conn:
        ensure_schema(conn)

    session_id = "s1"
    event_id = "e1"
    event1 = make_event(session_id, event_id, {"foo": 1}, "hash1")
    event2 = make_event(session_id, event_id, {"foo": 2}, "hash2")

    store.append(event1)
    with pytest.raises(EventConflictError) as excinfo:
        store.append(event2)
    err = excinfo.value
    assert err.session_id == session_id
    assert err.event_id == event_id
    assert err.existing_type == event1.type
    assert err.incoming_type == event2.type
    assert err.existing_hash == event1.payload_hash
    assert err.incoming_hash == event2.payload_hash

    db_path = tmp_path / "test.sqlite"
    store = SqliteEventStore(str(db_path))
    with store._connect() as conn:
        ensure_schema(conn)

    session_id = "s1"
    event_id = "e1"
    event1 = make_event(session_id, event_id, {"foo": 1}, "hash1", type_="QUOTE_INGESTED")
    event2 = make_event(session_id, event_id, {"foo": 1}, "hash1", type_="COMPUTE_REQUESTED")

    store.append(event1)
    with pytest.raises(EventConflictError) as excinfo:
        store.append(event2)
    err = excinfo.value
    assert err.session_id == session_id
    assert err.event_id == event_id
    assert err.existing_type == event1.type
    assert err.incoming_type == event2.type
    assert err.existing_hash == event1.payload_hash
    assert err.incoming_hash == event2.payload_hash
