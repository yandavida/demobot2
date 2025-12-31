
import sqlite3
import json
from datetime import datetime
from contextlib import closing
from core.v2.models import V2Event
from core.v2.persistence_config import get_v2_db_path, ensure_var_dir_exists
from core.v2.errors import EventConflictError

class SqliteEventStore:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = get_v2_db_path()
        self.db_path = db_path

    def _connect(self):
        from core.v2.sqlite_schema import run_migrations
        ensure_var_dir_exists(self.db_path)
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        run_migrations(conn)
        return conn

    def close(self):
        pass  # No-op: no long-lived connection

    def append(self, event: V2Event) -> bool:
        now = datetime.utcnow().isoformat()
        with closing(self._connect()) as conn, closing(conn.cursor()) as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO events (
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
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                cur.execute(
                    "SELECT type, payload_hash FROM events WHERE session_id = ? AND event_id = ?",
                    (event.session_id, event.event_id),
                )
                row = cur.fetchone()
                if row is None:
                    raise
                existing_type, existing_hash = row
                incoming_type = event.type
                incoming_hash = event.payload_hash
                if existing_hash == incoming_hash and existing_type == incoming_type:
                    return False
                raise EventConflictError(
                    event.session_id,
                    event.event_id,
                    existing_type,
                    incoming_type,
                    existing_hash,
                    incoming_hash,
                )

    def list(self, session_id: str, after_version: int | None = None, limit: int | None = None):
        with closing(self._connect()) as conn, closing(conn.cursor()) as cur:
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
