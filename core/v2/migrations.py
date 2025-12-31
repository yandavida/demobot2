import sqlite3

CURRENT_SCHEMA_VERSION = 1

def run_migrations(conn: sqlite3.Connection) -> None:
    """
    Idempotent migration entrypoint. Ensures schema exists and PRAGMA user_version is up-to-date.
    This function must NOT change schema definition. It only manages versioning via PRAGMA user_version.
    """
    cur = conn.cursor()
    cur.execute("PRAGMA user_version")
    user_version = cur.fetchone()[0]
    if user_version == 0:
        # Fresh DB: assume schema already exists, just set version
        cur.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")
    elif user_version < CURRENT_SCHEMA_VERSION:
        # Upgrade path (no-op for now, but place for future logic)
        cur.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")
    elif user_version > CURRENT_SCHEMA_VERSION:
        raise RuntimeError(f"DB user_version {user_version} > supported CURRENT_SCHEMA_VERSION {CURRENT_SCHEMA_VERSION}")
    conn.commit()
