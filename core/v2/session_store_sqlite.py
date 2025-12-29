import sqlite3
from datetime import datetime
from core.v2.sqlite_schema import ensure_schema
from core.v2.persistence_config import get_v2_db_path, ensure_var_dir_exists

class SqliteSessionStore:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = get_v2_db_path()
        ensure_var_dir_exists(db_path)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        ensure_schema(self.conn)

    def create(self, session_id: str, created_at: datetime) -> None:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO sessions (session_id, created_at)
                VALUES (?, ?)
                ON CONFLICT(session_id) DO NOTHING
                """,
                (session_id, created_at.isoformat()),
            )
            self.conn.commit()
        finally:
            cur.close()

    def exists(self, session_id: str) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute(
                "SELECT 1 FROM sessions WHERE session_id = ? LIMIT 1",
                (session_id,)
            )
            return cur.fetchone() is not None
        finally:
            cur.close()

    def get(self, session_id: str):
        cur = self.conn.cursor()
        try:
            cur.execute(
                "SELECT session_id, created_at FROM sessions WHERE session_id = ?",
                (session_id,)
            )
            row = cur.fetchone()
            if not row:
                return None
            return {"session_id": row[0], "created_at": row[1]}
        finally:
            cur.close()

    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            self.conn = None
