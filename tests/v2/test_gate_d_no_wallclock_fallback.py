import re
import pathlib
import pytest


def test_no_wallclock_fallback_for_event_ts_in_service_sqlite():
    p = pathlib.Path("api/v2/service_sqlite.py")
    assert p.exists(), "api/v2/service_sqlite.py missing"
    txt = p.read_text()

    # direct pattern: `ts or datetime.utcnow` or `event_ts = ts or datetime.utcnow()`
    if re.search(r"\bts\s*or\s*datetime\.utcnow", txt):
        pytest.fail("Found `ts or datetime.utcnow` pattern in api/v2/service_sqlite.py")

    # any occurrence of datetime.utcnow near ts-related tokens (within same line)
    for i, line in enumerate(txt.splitlines(), start=1):
        if "datetime.utcnow" in line and re.search(r"\b(ts|event_ts|event\.ts)\b", line):
            pytest.fail(f"Found datetime.utcnow used with ts on line {i}: {line.strip()}")

    # multi-line fallback: look for 'if ts is None' followed by datetime.utcnow within next 3 lines
    lines = txt.splitlines()
    for i, line in enumerate(lines):
        if re.search(r"\bif\s+ts\s+is\s+None\b", line):
            window = "\n".join(lines[i : i + 4])
            if "datetime.utcnow" in window:
                pytest.fail("Detected multi-line ts fallback using datetime.utcnow in api/v2/service_sqlite.py")
