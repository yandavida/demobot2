import sqlite3
from datetime import datetime
from core.v2.persistence_config import get_v2_db_path, ensure_var_dir_exists


from contextlib import closing

class SqliteSessionStore:
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

    def create(self, session_id: str, created_at: datetime) -> None:
        with closing(self._connect()) as conn, closing(conn.cursor()) as cur:
            cur.execute(
                """
                INSERT INTO sessions (session_id, created_at)
                VALUES (?, ?)
                ON CONFLICT(session_id) DO NOTHING
                """,
                (session_id, created_at.isoformat()),
            )
            conn.commit()

    def exists(self, session_id: str) -> bool:
        with closing(self._connect()) as conn, closing(conn.cursor()) as cur:
            cur.execute(
                "SELECT 1 FROM sessions WHERE session_id = ? LIMIT 1",
                (session_id,)
            )
            return cur.fetchone() is not None

    def get(self, session_id: str):
        with closing(self._connect()) as conn, closing(conn.cursor()) as cur:
            cur.execute(
                "SELECT session_id, created_at FROM sessions WHERE session_id = ?",
                (session_id,)
            )
            row = cur.fetchone()
            if not row:
                return None
            return {"session_id": row[0], "created_at": row[1]}

    def close(self):
        pass  # No-op: no long-lived connection
