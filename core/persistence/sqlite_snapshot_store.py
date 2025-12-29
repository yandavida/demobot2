"""
SQLite-backed implementation of SnapshotStore interface.
"""
from __future__ import annotations

import sqlite3
from typing import Optional, List
from datetime import datetime
import json
from core.v2.models import Snapshot, hash_snapshot, canonical_json
from .types import StorageError, StorageIntegrityError, StorageConnectionError
from .schema import run_migrations

class SqliteSnapshotStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        try:
            self.conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
            run_migrations(self.conn)
        except sqlite3.Error as e:
            raise StorageConnectionError(f"Failed to connect or migrate: {e}")

    def save(self, snapshot: Snapshot) -> None:
        try:
            cur = self.conn.cursor()
            payload_json = canonical_json(snapshot.data)
            # חשב hash דטרמיניסטי תמיד
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
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            raise StorageIntegrityError(f"Integrity error: {e}")
        except sqlite3.Error as e:
            raise StorageError(f"DB error: {e}")

    def get(self, session_id: str, version: int) -> Optional[Snapshot]:
        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT session_id, version, payload, payload_hash, created_at FROM snapshot_store WHERE session_id = ? AND version = ?",
                (session_id, version)
            )
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_snapshot(row)
        except sqlite3.Error as e:
            raise StorageError(f"DB error: {e}")

    def latest(self, session_id: str) -> Optional[Snapshot]:
        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT session_id, version, payload, payload_hash, created_at FROM snapshot_store WHERE session_id = ? ORDER BY version DESC LIMIT 1",
                (session_id,)
            )
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_snapshot(row)
        except sqlite3.Error as e:
            raise StorageError(f"DB error: {e}")

    def list(self, session_id: str) -> List[Snapshot]:
        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT session_id, version, payload, payload_hash, created_at FROM snapshot_store WHERE session_id = ? ORDER BY version ASC",
                (session_id,)
            )
            rows = cur.fetchall()
            return [self._row_to_snapshot(row) for row in rows]
        except sqlite3.Error as e:
            raise StorageError(f"DB error: {e}")

    def _row_to_snapshot(self, row) -> Snapshot:
        session_id, version, payload_json, state_hash, created_at = row
        data = json.loads(payload_json)
        # ודא hash דטרמיניסטי תמיד
        computed_hash = hash_snapshot(data)
        return Snapshot(
            session_id=session_id,
            version=version,
            created_at=datetime.fromisoformat(created_at),
            state_hash=computed_hash,
            data=data,
        )
