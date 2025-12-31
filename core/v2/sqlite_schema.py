import sqlite3


# === Schema sealed after v1; future changes must not modify schema ===
LATEST_SCHEMA_VERSION = 1

def run_migrations(conn: sqlite3.Connection) -> None:
    """
    Idempotent migration entrypoint. Ensures schema and schema_version table exist and are up-to-date.
    """
    cur = conn.cursor()
    # Create schema_version table if missing
    cur.execute('''
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    # If empty, insert version 1
    cur.execute("SELECT COUNT(*) FROM schema_version")
    if cur.fetchone()[0] == 0:
        from datetime import datetime
        cur.execute(
            "INSERT INTO schema_version(version, updated_at) VALUES (?, ?)",
            (LATEST_SCHEMA_VERSION, datetime.utcnow().isoformat()),
        )
    else:
        cur.execute("SELECT version FROM schema_version")
        version = cur.fetchone()[0]
        if version != LATEST_SCHEMA_VERSION:
            # For now, only support v1
            raise RuntimeError(f"DB schema version {version} != expected {LATEST_SCHEMA_VERSION}")
    # Ensure all other tables exist (idempotent)
    ensure_schema(conn)
    conn.commit()

def get_schema_version(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    try:
        cur.execute("SELECT version FROM schema_version")
        row = cur.fetchone()
        if row:
            return row[0]
        return 0
    except sqlite3.OperationalError:
        # Table missing
        return 0

def set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    from datetime import datetime
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    cur.execute("DELETE FROM schema_version")
    cur.execute(
        "INSERT INTO schema_version(version, updated_at) VALUES (?, ?)",
        (version, datetime.utcnow().isoformat()),
    )
    conn.commit()

SCHEMA_VERSION = LATEST_SCHEMA_VERSION

def ensure_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

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
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL
        )
    """)

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
