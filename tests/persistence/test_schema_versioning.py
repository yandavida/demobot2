import sqlite3
import tempfile
import os
from core.v2.sqlite_schema import (
    SCHEMA_VERSION,
    run_migrations,
    get_schema_version,
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
                v = get_schema_version(conn)
                assert v == SCHEMA_VERSION
    finally:
        os.remove(db_path)

def test_upgrade_from_empty_db_sets_version_to_latest():
    db_path = make_temp_db()
    try:
        with sqlite3.connect(db_path) as conn:
            run_migrations(conn)
            v = get_schema_version(conn)
            assert v == SCHEMA_VERSION
    finally:
        os.remove(db_path)

def test_schema_version_persists_across_connections():
    db_path = make_temp_db()
    try:
        with sqlite3.connect(db_path) as conn:
            run_migrations(conn)
        with sqlite3.connect(db_path) as conn:
            v = get_schema_version(conn)
            assert v == SCHEMA_VERSION
    finally:
        os.remove(db_path)
