import sqlite3
import sys

def print_snapshots(session_id):
    db_path = "var/v2.sqlite"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    print("Schema for snapshots table:")
    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name='snapshots'")
    for name, sql in cur.fetchall():
        print(f"Table: {name}\nSQL: {sql}")
    print("\nRows for session_id:", session_id)
    cur.execute("SELECT session_id, version, state_hash, length(data_json), created_at FROM snapshots WHERE session_id = ? ORDER BY version", (session_id,))
    for row in cur.fetchall():
        print(row)
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/inspect_snapshots.py <session_id>")
        sys.exit(1)
    print_snapshots(sys.argv[1])
