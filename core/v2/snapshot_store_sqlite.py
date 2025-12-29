
import json
import sqlite3
from datetime import datetime
from contextlib import closing

from core.v2.models import Snapshot
from core.v2.persistence_config import ensure_var_dir_exists, get_v2_db_path
from core.v2.sqlite_schema import ensure_schema


class SqliteSnapshotStore:

    """
    SQLite-backed snapshot store.

    Notes:
    - Orchestrator expects snapshot_store.save(snapshot)
    - Service expects snapshot_store.latest(session_id)
    We implement both as aliases to the canonical methods (put/get_latest).
    """


    from contextlib import closing

    def close(self):
        pass  # No-op: no long-lived connection


    def __init__(self, db_path: str | None = None) -> None:
        import logging
        if db_path is None:
            db_path = get_v2_db_path()
        self.db_path = db_path
        logging.getLogger("core.v2.snapshot_store_sqlite").debug(
            f"SqliteSnapshotStore: db_path={db_path}"
        )

    def _connect(self):
        ensure_var_dir_exists(self.db_path)
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        ensure_schema(conn)
        return conn

    # -------- Compatibility aliases --------

    def save(self, snapshot: Snapshot) -> None:
        """Alias ל-put עבור תאימות לאורקסטרטור."""
        self.put(snapshot)

    def latest(self, session_id: str) -> Snapshot | None:
        """Alias ל-get_latest עבור תאימות לשכבות השירות."""
        return self.get_latest(session_id)

    # -------- Canonical API --------


    def put(self, snapshot: Snapshot) -> None:
        import logging
        logger = logging.getLogger("core.v2.snapshot_store_sqlite")
        with closing(self._connect()) as conn, closing(conn.cursor()) as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO snapshots (
                        session_id, version, state_hash, data_json, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(session_id, version) DO NOTHING
                    """,
                    (
                        snapshot.session_id,
                        snapshot.version,
                        snapshot.state_hash,
                        json.dumps(
                            snapshot.data,
                            separators=(",", ":"),
                            sort_keys=True,
                            ensure_ascii=False,
                        ),
                        snapshot.created_at.isoformat(),
                    ),
                )
                conn.commit()
                logger.debug(
                    "put: session_id=%s version=%s state_hash=%s rowcount=%s",
                    snapshot.session_id,
                    snapshot.version,
                    snapshot.state_hash,
                    cur.rowcount,
                )
                cur.execute("SELECT COUNT(*) FROM snapshots WHERE session_id=?", (snapshot.session_id,))
                count = cur.fetchone()[0]
                logger.debug("put: snapshot count for session_id=%s: %s", snapshot.session_id, count)
            except Exception as e:
                logger.exception("put: EXCEPTION: %s", e)
                raise


    def get_latest(self, session_id: str) -> Snapshot | None:
        with closing(self._connect()) as conn, closing(conn.cursor()) as cur:
            cur.execute(
                """
                SELECT version, state_hash, data_json, created_at
                FROM snapshots
                WHERE session_id = ?
                ORDER BY version DESC
                LIMIT 1
                """,
                (session_id,),
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


    def get_at_or_before(self, session_id: str, version: int) -> Snapshot | None:
        with closing(self._connect()) as conn, closing(conn.cursor()) as cur:
            cur.execute(
                """
                SELECT version, state_hash, data_json, created_at
                FROM snapshots
                WHERE session_id = ? AND version <= ?
                ORDER BY version DESC
                LIMIT 1
                """,
                (session_id, version),
            )
            row = cur.fetchone()
            if not row:
                return None
            ver, state_hash, data_json, created_at = row
            return Snapshot(
                session_id=session_id,
                version=ver,
                state_hash=state_hash,
                data=json.loads(data_json),
                created_at=datetime.fromisoformat(created_at),
            )
