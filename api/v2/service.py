



import os
from core.v2.persistence_config import get_v2_db_path
from api.v2.service_sqlite import V2ServiceSqlite

_FORCE_RAISE_FOR_TESTS = False
_V2_SERVICE = None

def get_v2_service():
    global _V2_SERVICE
    if _V2_SERVICE is None:
        _V2_SERVICE = V2ServiceSqlite()
    return _V2_SERVICE

def enable_force_raise_for_tests(enabled: bool) -> None:
    global _FORCE_RAISE_FOR_TESTS
    _FORCE_RAISE_FOR_TESTS = bool(enabled)

def should_force_raise_for_tests() -> bool:
    return _FORCE_RAISE_FOR_TESTS

def reset_for_tests() -> None:
    global _V2_SERVICE, _FORCE_RAISE_FOR_TESTS
    _FORCE_RAISE_FOR_TESTS = False
    if _V2_SERVICE is not None:
        try:
            _V2_SERVICE.close()
        except Exception:
            pass
        _V2_SERVICE = None
    db_path = get_v2_db_path()
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

__all__ = [
    "get_v2_service",
    "enable_force_raise_for_tests",
    "reset_for_tests",
    "should_force_raise_for_tests",
]
