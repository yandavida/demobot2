import sqlite3

def print_tables_and_schema():
    db_path = "var/v2.sqlite"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    print("All tables and their schema:")
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for (name,) in cur.fetchall():
        print("Table: {}".format(name))
        cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (name,))
        for (sql,) in cur.fetchall():
            print(sql)
    conn.close()

if __name__ == "__main__":
    print_tables_and_schema()
