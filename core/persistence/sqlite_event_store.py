"""
SQLite-backed implementation of EventStore interface.
"""
from __future__ import annotations

import sqlite3
from typing import List
from datetime import datetime
import json
from core.v2.models import V2Event
from .types import StorageError, StorageIntegrityError, StorageConnectionError
from .schema import run_migrations

class SqliteEventStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        try:
            self.conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
            run_migrations(self.conn)
        except sqlite3.Error as e:
            raise StorageConnectionError(f"Failed to connect or migrate: {e}")

    def append(self, event: V2Event) -> None:
        """Append an event to the store. Idempotent: if event exists, no-op. If conflict, raise."""
        try:
            cur = self.conn.cursor()
            # בדוק idempotency לפי (session_id, event_id)
            cur.execute(
                "SELECT type, payload, seq FROM event_store WHERE session_id = ? AND event_id = ?",
                (event.session_id, event.event_id),
            )
            row = cur.fetchone()
            if row:
                # אם האירוע קיים וזהה, no-op
                if row[0] == event.type and row[1] == json.dumps(event.payload, separators=(",", ":")):
                    return
                # אם קיים אבל שונה, זו התנגשות
                raise StorageIntegrityError(f"Event conflict for session_id={event.session_id} event_id={event.event_id}")
            # חשב seq הבא (הגרסה)
            cur.execute(
                "SELECT COALESCE(MAX(seq), 0) + 1 FROM event_store WHERE session_id = ?",
                (event.session_id,)
            )
            next_seq = cur.fetchone()[0]
            # הוסף אירוע
            cur.execute(
                """
                INSERT INTO event_store (session_id, seq, event_id, ts, type, payload, payload_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.session_id,
                    next_seq,
                    event.event_id,
                    event.ts.isoformat(),
                    event.type,
                    json.dumps(event.payload, separators=(",", ":")),
                    event.payload_hash,
                    datetime.now().isoformat(),
                ),
            )
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            raise StorageIntegrityError(f"Integrity error: {e}")
        except sqlite3.Error as e:
            raise StorageError(f"DB error: {e}")

    def list(self, session_id: str) -> List[V2Event]:
        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT event_id, session_id, ts, type, payload, payload_hash FROM event_store WHERE session_id = ? ORDER BY seq ASC",
                (session_id,)
            )
            rows = cur.fetchall()
            return [self._row_to_event(row) for row in rows]
        except sqlite3.Error as e:
            raise StorageError(f"DB error: {e}")

    def list_after_version(self, session_id: str, after_version: int) -> List[V2Event]:
        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT event_id, session_id, ts, type, payload, payload_hash FROM event_store WHERE session_id = ? AND seq > ? ORDER BY seq ASC",
                (session_id, after_version)
            )
            rows = cur.fetchall()
            return [self._row_to_event(row) for row in rows]
        except sqlite3.Error as e:
            raise StorageError(f"DB error: {e}")

    def _row_to_event(self, row) -> V2Event:
        event_id, session_id, ts, type_, payload_json, payload_hash = row
        return V2Event(
            event_id=event_id,
            session_id=session_id,
            ts=datetime.fromisoformat(ts),
            type=type_,
            payload=json.loads(payload_json),
            payload_hash=payload_hash,
        )
