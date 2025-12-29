"""
Minimal V2 persistence schema contract.
"""

def run_migrations(conn):
    """Create minimal tables for events and snapshots. Idempotent."""
    cur = conn.cursor()
    # Events table
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
    # Snapshots table
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
    cur.close()
