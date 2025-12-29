

import os
from core.v2.persistence_config import get_v2_db_path
from api.v2.service_sqlite import V2ServiceSqlite

_FORCE_RAISE_FOR_TESTS = False
_v2_service = None

def _build_v2_service():
    return V2ServiceSqlite()

# Canonical singleton instance for contract
v2_service = _build_v2_service()

def get_v2_service():
    return v2_service

def enable_force_raise_for_tests(enabled: bool) -> None:
    global _FORCE_RAISE_FOR_TESTS
    _FORCE_RAISE_FOR_TESTS = bool(enabled)

def should_force_raise_for_tests() -> bool:
    return _FORCE_RAISE_FOR_TESTS

def reset_for_tests() -> None:
    global _FORCE_RAISE_FOR_TESTS
    _FORCE_RAISE_FOR_TESTS = False
    # Reset the singleton instance to a clean state
    if hasattr(v2_service, "close"):
        try:
            v2_service.close()
        except Exception:
            pass
    # Remove and recreate the DB file for a clean slate
    db_path = get_v2_db_path()
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

__all__ = [
    "v2_service",
    "get_v2_service",
    "enable_force_raise_for_tests",
    "reset_for_tests",
    "should_force_raise_for_tests",
]
