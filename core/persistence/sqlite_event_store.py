"""
SQLite-backed implementation of EventStore interface.
"""
from __future__ import annotations

import sqlite3
import json
from datetime import datetime
from typing import List
from contextlib import closing
from core.v2.models import V2Event

class SqliteEventStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Ensure schema at construction
        with self._connect() as conn:
            self._ensure_schema(conn)

    def _connect(self):
        return sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)

    def _ensure_schema(self, conn):
        with closing(conn.cursor()) as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS event_store (
                    session_id TEXT NOT NULL,
                    seq INTEGER NOT NULL,
                    event_id TEXT NOT NULL,
                    ts TEXT NOT NULL,
                    type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (session_id, event_id)
                )
            ''')
            conn.commit()

    def append(self, event: V2Event) -> None:
        with self._connect() as conn, closing(conn.cursor()) as cur:
            self._ensure_schema(conn)
            cur.execute(
                "SELECT type, payload FROM event_store WHERE session_id = ? AND event_id = ?",
                (event.session_id, event.event_id),
            )
            row = cur.fetchone()
            if row:
                # If event exists and is identical, no-op
                if row[0] == event.type and row[1] == json.dumps(event.payload, separators=(",", ":")):
                    return
                # If exists but different, raise
                raise sqlite3.IntegrityError(f"Event conflict for session_id={event.session_id} event_id={event.event_id}")
            cur.execute(
                "SELECT COALESCE(MAX(seq), 0) + 1 FROM event_store WHERE session_id = ?",
                (event.session_id,)
            )
            next_seq = cur.fetchone()[0]
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
            conn.commit()

    def list_after_version(self, session_id: str, after_version: int) -> List[V2Event]:
        with self._connect() as conn, closing(conn.cursor()) as cur:
            self._ensure_schema(conn)
            cur.execute(
                "SELECT event_id, session_id, ts, type, payload, payload_hash FROM event_store WHERE session_id = ? AND seq > ? ORDER BY seq ASC",
                (session_id, after_version)
            )
            rows = cur.fetchall()
            return [self._row_to_event(row) for row in rows]

    def list(self, session_id: str) -> List[V2Event]:
        with self._connect() as conn, closing(conn.cursor()) as cur:
            self._ensure_schema(conn)
            cur.execute(
                "SELECT event_id, session_id, ts, type, payload, payload_hash FROM event_store WHERE session_id = ? ORDER BY seq ASC",
                (session_id,)
            )
            rows = cur.fetchall()
            return [self._row_to_event(row) for row in rows]

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
