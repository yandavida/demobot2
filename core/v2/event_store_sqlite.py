import sqlite3
import json
from datetime import datetime
from core.v2.models import V2Event
from core.v2.sqlite_schema import ensure_schema
from core.v2.persistence_config import V2_DB_PATH, ensure_var_dir_exists

class SqliteEventStore:
    def __init__(self, db_path: str = V2_DB_PATH):
        ensure_var_dir_exists()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        ensure_schema(self.conn)

    def append(self, event: V2Event) -> bool:
        cur = self.conn.cursor()
        now = datetime.utcnow().isoformat()
        try:
            cur.execute(
                """
                INSERT OR IGNORE INTO events (
                    session_id, event_id, ts, type, payload_json, payload_hash, inserted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.session_id,
                    event.event_id,
                    event.ts.isoformat(),
                    event.type,
                    json.dumps(event.payload, separators=(",", ":"), sort_keys=True, ensure_ascii=False),
                    event.payload_hash,
                    now,
                ),
            )
            self.conn.commit()
            return cur.rowcount == 1
        finally:
            cur.close()

    def list(self, session_id: str, after_version: int | None = None, limit: int | None = None):
        cur = self.conn.cursor()
        try:
            q = "SELECT event_id, ts, type, payload_json, payload_hash FROM events WHERE session_id = ? ORDER BY ts, event_id"
            params = [session_id]
            # after_version/limit not implemented for now (API compatibility)
            cur.execute(q, params)
            rows = cur.fetchall()
            events = []
            for event_id, ts, type_, payload_json, payload_hash in rows:
                events.append(V2Event(
                    event_id=event_id,
                    session_id=session_id,
                    ts=datetime.fromisoformat(ts),
                    type=type_,
                    payload=json.loads(payload_json),
                    payload_hash=payload_hash,
                ))
            return events
        finally:
            cur.close()
