import pytest
from datetime import datetime
from core.v2.event_store_sqlite import SqliteEventStore
from core.v2.snapshot_store_sqlite import SqliteSnapshotStore
from core.v2.models import V2Event, Snapshot, hash_payload

@pytest.fixture
def temp_db_path(tmp_path):
    db_path = tmp_path / "v2test.db"
    return str(db_path)

def make_event(session_id, event_id, ts, type_, payload):
    return V2Event(
        event_id=event_id,
        session_id=session_id,
        ts=ts,
        type=type_,
        payload=payload,
        payload_hash=hash_payload(payload),
    )

def make_snapshot(session_id, version, state_hash, data, created_at):
    return Snapshot(
        session_id=session_id,
        version=version,
        state_hash=state_hash,
        data=data,
        created_at=created_at,
    )

def test_restart_roundtrip_determinism(temp_db_path):
    session_id = "sess1"
    event_store = SqliteEventStore(temp_db_path)
    events = [
        make_event(session_id, f"evt{i}", datetime(2025, 1, 1, 12, 0, i), "QUOTE_INGESTED", {"val": i})
        for i in range(3)
    ]
    for e in events:
        event_store.append(e)
    # Read back
    events_out = event_store.list(session_id)
    assert [e.event_id for e in events_out] == [e.event_id for e in events]
    # Simulate restart
    event_store2 = SqliteEventStore(temp_db_path)
    events_out2 = event_store2.list(session_id)
    assert [e.event_id for e in events_out2] == [e.event_id for e in events]

def test_idempotent_event_insert(temp_db_path):
    session_id = "sess2"
    event_store = SqliteEventStore(temp_db_path)
    e = make_event(session_id, "evt1", datetime.utcnow(), "QUOTE_INGESTED", {"foo": 1})
    applied1 = event_store.append(e)
    applied2 = event_store.append(e)
    assert applied1 is True
    assert applied2 is False
    events = event_store.list(session_id)
    assert len(events) == 1
    assert events[0].event_id == "evt1"

def test_snapshot_latest_roundtrip(temp_db_path):
    session_id = "sess3"
    snap_store = SqliteSnapshotStore(temp_db_path)
    snap = make_snapshot(session_id, 1, "hash1", {"foo": 1}, datetime.utcnow())
    snap_store.put(snap)
    latest = snap_store.get_latest(session_id)
    assert latest is not None
    assert latest.version == 1
    assert latest.state_hash == "hash1"
    # Simulate restart
    snap_store2 = SqliteSnapshotStore(temp_db_path)
    latest2 = snap_store2.get_latest(session_id)
    assert latest2 is not None
    assert latest2.version == 1
    assert latest2.state_hash == "hash1"
