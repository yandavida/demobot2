import sqlite3

SCHEMA_VERSION = 1

def ensure_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS schema_meta (
            version INTEGER NOT NULL
        )
    """)
    cur.execute("SELECT COUNT(*) FROM schema_meta")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO schema_meta(version) VALUES (?)", (SCHEMA_VERSION,))
    else:
        cur.execute("SELECT version FROM schema_meta")
        version = cur.fetchone()[0]
        if version != SCHEMA_VERSION:
            raise RuntimeError(f"DB schema version {version} != expected {SCHEMA_VERSION}")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            session_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            ts TEXT NOT NULL,
            type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            inserted_at TEXT NOT NULL,
            PRIMARY KEY (session_id, event_id)
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_events_session_ts ON events(session_id, ts)")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            session_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            state_hash TEXT NOT NULL,
            data_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (session_id, version)
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_session_version ON snapshots(session_id, version)")
    conn.commit()
