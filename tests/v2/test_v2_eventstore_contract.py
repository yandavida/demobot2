import tempfile
import os
from datetime import datetime
from core.v2.event_store_sqlite import SqliteEventStore
from core.v2.models import V2Event

def make_temp_db():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    return path

def test_list_after_version_applied_version_contract():
    db_path = make_temp_db()
    try:
        session_id = "contract-gap"
        store = SqliteEventStore(db_path)
        # צור אירועים עם event_id ייחודי, סדר דטרמיניסטי
        events = [
            V2Event(event_id="a", session_id=session_id, ts=datetime(2025,1,1,12,0,0), type="QUOTE_INGESTED", payload={"v":1}, payload_hash="1"),
            V2Event(event_id="b", session_id=session_id, ts=datetime(2025,1,1,12,0,1), type="QUOTE_INGESTED", payload={"v":2}, payload_hash="2"),
            V2Event(event_id="c", session_id=session_id, ts=datetime(2025,1,1,12,0,2), type="QUOTE_INGESTED", payload={"v":3}, payload_hash="3"),
            V2Event(event_id="d", session_id=session_id, ts=datetime(2025,1,1,12,0,3), type="QUOTE_INGESTED", payload={"v":4}, payload_hash="4"),
        ]
        for e in events:
            store.append(e)
        # מחק את האירוע השני ("b") ישירות מה-DB כדי ליצור gap ב-applied_version
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            conn.execute("DELETE FROM events WHERE event_id = ? AND session_id = ?", ("b", session_id))
            conn.commit()
        # כעת applied_version: a=1, c=2, d=3
        # list_after_version(session_id, 1) אמור להחזיר c,d בלבד
        tail = store.list_after_version(session_id, 1)
        tail_ids = [e.event_id for e in tail]
        assert tail_ids == ["c", "d"], f"Expected ['c', 'd'], got {tail_ids}"
    finally:
        os.remove(db_path)
