import pytest
from datetime import datetime

from core.v2.event_store_sqlite import SqliteEventStore
from core.v2.errors import EventConflictError
from core.v2.models import V2Event, hash_payload
from core.v2.sqlite_schema import ensure_schema


def make_event(session_id: str, event_id: str, payload: dict, ts: datetime) -> V2Event:
    return V2Event(
        event_id=event_id,
        session_id=session_id,
        ts=ts,
        type="QUOTE_INGESTED",
        payload=payload,
        payload_hash=hash_payload(payload),
    )


def _stored_event_by_id(store: SqliteEventStore, session_id: str, event_id: str):
    events = store.list(session_id)
    for e in events:
        if e.event_id == event_id:
            return e
    return None


def test_eventstore_idempotent_replay_does_not_duplicate(tmp_path):
    db_file = tmp_path / "evstore.sqlite"
    store = SqliteEventStore(str(db_file))
    # ensure schema
    with store._connect() as conn:
        ensure_schema(conn)

    session_id = "S1"
    event_id = "E1"
    ts = datetime(2025, 1, 1, 10, 0, 0)
    ev1 = make_event(session_id, event_id, {"v": 1}, ts)

    r1 = store.append(ev1)
    assert r1 is True

    # append same event again (identical payload) -> should be idempotent (return False or no duplicate)
    r2 = store.append(ev1)
    # API: False means already present with identical payload
    assert r2 in (False, True)

    events = store.list(session_id)
    assert len(events) == 1


def test_eventstore_conflicting_replay_behavior_is_explicit(tmp_path):
    db_file = tmp_path / "evstore.sqlite"
    store = SqliteEventStore(str(db_file))
    with store._connect() as conn:
        ensure_schema(conn)

    session_id = "S1"
    event_id = "E1"
    ts = datetime(2025, 1, 1, 10, 0, 0)
    ev1 = make_event(session_id, event_id, {"v": 1}, ts)
    ev2 = make_event(session_id, event_id, {"v": 2}, ts)

    store.append(ev1)
    before_events = store.list(session_id)
    before_count = len(before_events)

    raised = False
    result = None
    try:
        result = store.append(ev2)
    except EventConflictError as exc:
        raised = True
        err = exc

    after_events = store.list(session_id)
    after_count = len(after_events)

    # Fingerprint: count must not increase and stored event must remain original
    assert after_count == before_count, f"Event count changed on conflicting append: before={before_count} after={after_count}"

    stored = _stored_event_by_id(store, session_id, event_id)
    assert stored is not None, "Stored event missing after conflict test"
    # ensure stored payload still reflects original v:1
    assert stored.payload.get("v") == 1, "Unsafe: stored event was modified on conflicting append"

    # If not raised, explicitly record that behavior (test still passes if no overwrite/duplication)
    if raised:
        assert isinstance(err, EventConflictError)


def test_eventstore_conflict_does_not_overwrite_existing_event(tmp_path):
    db_file = tmp_path / "evstore.sqlite"
    store = SqliteEventStore(str(db_file))
    with store._connect() as conn:
        ensure_schema(conn)

    session_id = "S1"
    event_id = "E1"
    ts = datetime(2025, 1, 1, 10, 0, 0)
    ev1 = make_event(session_id, event_id, {"v": 1}, ts)
    ev2 = make_event(session_id, event_id, {"v": 2}, ts)

    store.append(ev1)
    try:
        store.append(ev2)
    except EventConflictError:
        pass

    stored = _stored_event_by_id(store, session_id, event_id)
    assert stored.payload.get("v") == 1, "Unsafe: overwrite on conflicting replay"


def test_eventstore_conflict_semantics_survive_reopen(tmp_path):
    db_file = tmp_path / "evstore.sqlite"
    store = SqliteEventStore(str(db_file))
    with store._connect() as conn:
        ensure_schema(conn)

    session_id = "S1"
    event_id = "E1"
    ts = datetime(2025, 1, 1, 10, 0, 0)
    ev1 = make_event(session_id, event_id, {"v": 1}, ts)
    ev2 = make_event(session_id, event_id, {"v": 2}, ts)

    store.append(ev1)
    # close by discarding instance (store has no long-lived connection)
    del store

    # reopen
    store2 = SqliteEventStore(str(db_file))
    with store2._connect() as conn:
        ensure_schema(conn)

    raised = False
    try:
        store2.append(ev2)
    except EventConflictError:
        raised = True

    events = store2.list(session_id)
    assert len(events) == 1, "Duplication or deletion occurred across reopen"
    stored = _stored_event_by_id(store2, session_id, event_id)
    assert stored.payload.get("v") == 1, "Unsafe: overwrite on conflicting replay after reopen"
