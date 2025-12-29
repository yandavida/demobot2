import sqlite3

def print_tables():
    db_path = "var/v2.sqlite"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    print("All tables:")
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for (name,) in cur.fetchall():
        print(name)
    conn.close()

if __name__ == "__main__":
    print_tables()
