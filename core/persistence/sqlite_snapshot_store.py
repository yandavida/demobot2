"""
SQLite-backed implementation of SnapshotStore interface.
"""
from __future__ import annotations

import sqlite3
import json
from datetime import datetime
from typing import Optional, List
from contextlib import closing
from core.v2.models import Snapshot, hash_snapshot

class SqliteSnapshotStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        with self._connect() as conn:
            self._ensure_schema(conn)

    def _connect(self):
        return sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)

    def _ensure_schema(self, conn):
        with closing(conn.cursor()) as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS snapshot_store (
                    session_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (session_id, version)
                )
            ''')
            conn.commit()

    def save(self, snapshot: Snapshot) -> None:
        with self._connect() as conn, closing(conn.cursor()) as cur:
            self._ensure_schema(conn)
            payload_json = json.dumps(snapshot.data, sort_keys=True, separators=(",", ":"))
            state_hash = hash_snapshot(snapshot.data)
            created_at = snapshot.created_at.isoformat()
            cur.execute(
                """
                INSERT OR REPLACE INTO snapshot_store (session_id, version, payload, payload_hash, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    snapshot.session_id,
                    snapshot.version,
                    payload_json,
                    state_hash,
                    created_at,
                ),
            )
            conn.commit()

    def latest(self, session_id: str) -> Optional[Snapshot]:
        with self._connect() as conn, closing(conn.cursor()) as cur:
            self._ensure_schema(conn)
            cur.execute(
                "SELECT session_id, version, payload, payload_hash, created_at FROM snapshot_store WHERE session_id = ? ORDER BY version DESC LIMIT 1",
                (session_id,)
            )
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_snapshot(row)

    def _row_to_snapshot(self, row) -> Snapshot:
        session_id, version, payload_json, state_hash, created_at = row
        data = json.loads(payload_json)
        computed_hash = hash_snapshot(data)
        return Snapshot(
            session_id=session_id,
            version=version,
            created_at=datetime.fromisoformat(created_at),
            state_hash=computed_hash,
            data=data,
        )
