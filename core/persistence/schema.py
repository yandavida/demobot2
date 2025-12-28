"""
DDL, schema versioning, and migration runner for SQLite persistence.
"""
import sqlite3

SCHEMA_VERSION = 1

DDL = [
    # Event store table
    '''
    CREATE TABLE IF NOT EXISTS event_store (
        session_id TEXT NOT NULL,
        seq INTEGER NOT NULL,
        event_id TEXT NOT NULL,
        ts TEXT NOT NULL,
        type TEXT NOT NULL,
        payload TEXT NOT NULL,
        payload_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (session_id, seq)
    );
    ''',
    # Snapshot store table
    '''
    CREATE TABLE IF NOT EXISTS snapshot_store (
        session_id TEXT NOT NULL,
        version INTEGER NOT NULL,
        payload TEXT NOT NULL,
        payload_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (session_id, version)
    );
    ''',
    # Schema version table
    '''
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER NOT NULL
    );
    '''
]

def run_migrations(conn: sqlite3.Connection):
    cur = conn.cursor()
    for ddl in DDL:
        cur.execute(ddl)
    # Ensure schema_version row exists
    cur.execute('SELECT COUNT(*) FROM schema_version')
    if cur.fetchone()[0] == 0:
        cur.execute('INSERT INTO schema_version (version) VALUES (?)', (SCHEMA_VERSION,))
    conn.commit()
