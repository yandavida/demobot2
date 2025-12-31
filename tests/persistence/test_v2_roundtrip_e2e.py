import tempfile
import os
from datetime import datetime, timedelta
from api.v2.service_sqlite import V2ServiceSqlite
from core.v2.models import hash_snapshot

def test_roundtrip_e2e():
    fd, db_path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    try:
        svc = V2ServiceSqlite(str(db_path))
        session_id = svc.create_session()
        base_ts = datetime(2025, 1, 1, 14, 0, 0)
        for i in range(10):
            svc.ingest_event(
                session_id=session_id,
                event_id=f"e{i}",
                ts=base_ts + timedelta(seconds=i),
                type="QUOTE_INGESTED",
                payload={"val": i},
            )
        snap1 = svc.get_snapshot(session_id)
        hash1 = hash_snapshot(snap1.data)
        # סגור ופתח מחדש
        svc.close()
        svc2 = V2ServiceSqlite(str(db_path))
        snap2 = svc2.get_snapshot(session_id)
        hash2 = hash_snapshot(snap2.data)
        assert hash1 == hash2
        # בדוק שכל האירועים קיימים ב-snapshot
        keys = set(snap2.data.keys())
        assert keys == {f"e{i}" for i in range(10)}
    finally:
        os.remove(db_path)
