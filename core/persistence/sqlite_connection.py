import sqlite3

def connect(db_path: str) -> sqlite3.Connection:
    """
    Open a SQLite connection with consistent PRAGMAs for all persistence stores.
    - foreign_keys=ON: Enforce FK constraints
    - journal_mode=WAL: Better concurrency
    - synchronous=NORMAL: Good balance of durability/performance
    - busy_timeout=5000ms: Wait for locks
    - temp_store=MEMORY: (optional, for temp tables)
    """
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn
