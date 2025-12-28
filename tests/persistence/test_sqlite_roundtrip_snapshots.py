from datetime import datetime
from core.persistence.sqlite_snapshot_store import SqliteSnapshotStore
from core.v2.models import Snapshot, hash_snapshot

def make_snapshot(session_id, version, data, created_at=None):
    if created_at is None:
        created_at = datetime.utcnow()
    return Snapshot(
        session_id=session_id,
        version=version,
        created_at=created_at,
        state_hash=hash_snapshot(data),
        data=data,
    )

def test_sqlite_snapshot_roundtrip(tmp_path):
    db_path = str(tmp_path / "snaps.db")
    store = SqliteSnapshotStore(db_path)
    session_id = "sess1"
    snap = make_snapshot(session_id, 1, {"foo": 1})
    store.save(snap)
    latest = store.latest(session_id)
    assert latest is not None
    assert latest.version == 1
    assert latest.state_hash == snap.state_hash
    # Simulate restart
    store2 = SqliteSnapshotStore(db_path)
    latest2 = store2.latest(session_id)
    assert latest2 is not None
    assert latest2.version == 1
    assert latest2.state_hash == snap.state_hash
