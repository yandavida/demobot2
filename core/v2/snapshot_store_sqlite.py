import sqlite3
import json
from datetime import datetime
from core.v2.models import Snapshot
from core.v2.sqlite_schema import ensure_schema
from core.v2.persistence_config import V2_DB_PATH, ensure_var_dir_exists

class SqliteSnapshotStore:
    def __init__(self, db_path: str = V2_DB_PATH):
        ensure_var_dir_exists()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        ensure_schema(self.conn)

    def put(self, snapshot: Snapshot) -> None:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO snapshots (
                    session_id, version, state_hash, data_json, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    snapshot.session_id,
                    snapshot.version,
                    snapshot.state_hash,
                    json.dumps(snapshot.data, separators=(",", ":"), sort_keys=True, ensure_ascii=False),
                    snapshot.created_at.isoformat(),
                ),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise RuntimeError("Snapshot version conflict: version must be monotonic and unique per session")
        finally:
            cur.close()

    def get_latest(self, session_id: str) -> Snapshot | None:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                SELECT version, state_hash, data_json, created_at FROM snapshots
                WHERE session_id = ?
                ORDER BY version DESC LIMIT 1
                """,
                (session_id,)
            )
            row = cur.fetchone()
            if not row:
                return None
            version, state_hash, data_json, created_at = row
            return Snapshot(
                session_id=session_id,
                version=version,
                state_hash=state_hash,
                data=json.loads(data_json),
                created_at=datetime.fromisoformat(created_at),
            )
        finally:
            cur.close()

    def get_at_or_before(self, session_id: str, version: int) -> Snapshot | None:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                SELECT version, state_hash, data_json, created_at FROM snapshots
                WHERE session_id = ? AND version <= ?
                ORDER BY version DESC LIMIT 1
                """,
                (session_id, version)
            )
            row = cur.fetchone()
            if not row:
                return None
            version, state_hash, data_json, created_at = row
            return Snapshot(
                session_id=session_id,
                version=version,
                state_hash=state_hash,
                data=json.loads(data_json),
                created_at=datetime.fromisoformat(created_at),
            )
        finally:
            cur.close()
