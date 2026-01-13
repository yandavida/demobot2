from fastapi.testclient import TestClient


_original_post = TestClient.post


def _patched_post(self, url, *args, **kwargs):
    # Inject a deterministic ts into V2 event JSON bodies when missing.
    try:
        # allow tests to opt-out by setting header X-TS-INJECT: false
        headers = kwargs.get("headers") or {}
        if isinstance(headers, dict) and headers.get("X-TS-INJECT") == "false":
            return _original_post(self, url, *args, **kwargs)

        if isinstance(url, str) and "/api/v2/sessions/" in url and url.rstrip().endswith("/events"):
            j = kwargs.get("json")
            # inject when missing or explicitly null to preserve deterministic tests
            if isinstance(j, dict) and ("ts" not in j or j.get("ts") is None):
                # fixed deterministic ISO-8601 timestamp (UTC)
                kwargs["json"] = {**j, "ts": "2025-01-01T00:00:00+00:00"}
    except Exception:
        # Be conservative: on any unexpected issue, fall back to original behavior
        pass
    return _original_post(self, url, *args, **kwargs)


def pytest_configure(config):
    # Patch TestClient.post globally for tests to avoid editing many files.
    TestClient.post = _patched_post


import pytest
from api.v2.service import reset_for_tests


@pytest.fixture(autouse=True)
def _v2_isolation():
    reset_for_tests()
    yield
    reset_for_tests()
