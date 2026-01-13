from __future__ import annotations

from datetime import datetime, timezone

import pytest

from api.v2.service_sqlite import V2ServiceSqlite
from core.validation.error_envelope import ErrorEnvelope


def _assert_validation_missing_ts(exc: Exception) -> None:
    # Service raises ValueError(ErrorEnvelope) pattern (institutional style).
    assert isinstance(exc, ValueError)
    envelope = exc.args[0]
    assert isinstance(envelope, ErrorEnvelope)
    assert envelope.category == "VALIDATION"
    # code may be project-specific; enforce at least non-empty & stable category
    assert isinstance(envelope.code, str) and envelope.code


def test_ingest_event_missing_ts_rejected(tmp_path) -> None:
    svc = V2ServiceSqlite(db_path=str(tmp_path / "v2.sqlite"))

    # Ensure session exists
    session_id = svc.create_session()

    with pytest.raises(Exception) as e:
        svc.ingest_event(
            session_id=session_id,
            event_id=None,
            ts=None,
            type="COMPUTE_REQUESTED",
            payload={"foo": 1},
        )
    _assert_validation_missing_ts(e.value)


def test_ingest_event_with_ts_ok(tmp_path) -> None:
    svc = V2ServiceSqlite(db_path=str(tmp_path / "v2.sqlite"))
    session_id = svc.create_session()

    fixed_ts = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    res = svc.ingest_event(
        session_id=session_id,
        event_id="evt_fixed",
        ts=fixed_ts,
        type="COMPUTE_REQUESTED",
        payload={"foo": 1},
    )

    # Minimal assertion: call succeeded and event persisted with exact ts
    events = svc.event_store.list(session_id=session_id)
    assert any(e.event_id == "evt_fixed" and e.ts == fixed_ts for e in events)
    assert res is not None
