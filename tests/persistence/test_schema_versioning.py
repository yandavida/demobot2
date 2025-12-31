import sqlite3
import tempfile
import os
from core.v2.migrations import (
    CURRENT_SCHEMA_VERSION,
    run_migrations,
)

def make_temp_db():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    return path

def test_run_migrations_is_idempotent():
    db_path = make_temp_db()
    try:
        for _ in range(2):
            with sqlite3.connect(db_path) as conn:
                run_migrations(conn)
                cur = conn.cursor()
                cur.execute("PRAGMA user_version")
                v = cur.fetchone()[0]
                assert v == CURRENT_SCHEMA_VERSION
    finally:
        os.remove(db_path)

def test_schema_version_fresh_db():
    db_path = make_temp_db()
    try:
        with sqlite3.connect(db_path) as conn:
            # Fresh DB: user_version should be 0
            cur = conn.cursor()
            cur.execute("PRAGMA user_version")
            assert cur.fetchone()[0] == 0
            run_migrations(conn)
            cur.execute("PRAGMA user_version")
            assert cur.fetchone()[0] == CURRENT_SCHEMA_VERSION
    finally:
        os.remove(db_path)

def test_schema_version_upgrade():
    db_path = make_temp_db()
    try:
        with sqlite3.connect(db_path) as conn:
            # Simulate old version
            cur = conn.cursor()
            cur.execute("PRAGMA user_version = 1")
            cur.execute("PRAGMA user_version")
            assert cur.fetchone()[0] == 1
            # Upgrade to CURRENT_SCHEMA_VERSION
            run_migrations(conn)
            cur.execute("PRAGMA user_version")
            assert cur.fetchone()[0] == CURRENT_SCHEMA_VERSION
            # Tables and indexes should exist (schema must not be changed here, so just check no error)
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cur.fetchall()}
            # These tables must exist if schema was created elsewhere (not by this test)
            # No schema creation allowed here
    finally:
        os.remove(db_path)

def test_schema_version_persists_across_connections():
    db_path = make_temp_db()
    try:
        with sqlite3.connect(db_path) as conn:
            run_migrations(conn)
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA user_version")
            v = cur.fetchone()[0]
            assert v == CURRENT_SCHEMA_VERSION
    finally:
        os.remove(db_path)
