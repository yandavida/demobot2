from core.validation.ingest_event_structural import (
    IngestEventCommand, IngestEventPayload, validate_ingest_event_command, ErrorEnvelope
)

def valid_cmd():
    payload = IngestEventPayload(event_type="SOME_EVENT", data={"foo": 1, "bar": "baz"})
    return IngestEventCommand(
        command_id="cmd-1",
        session_id="sess-1",
        kind="INGEST_EVENT",
        payload=payload,
        strict=True,
        meta=None,
    )

def test_valid_command_passes():
    cmd = valid_cmd()
    assert validate_ingest_event_command(cmd) is None

def test_missing_command_id():
    cmd = valid_cmd()
    cmd = cmd.__class__(
        command_id="",
        session_id=cmd.session_id,
        kind=cmd.kind,
        payload=cmd.payload,
        strict=cmd.strict,
        meta=cmd.meta,
    )
    err = validate_ingest_event_command(cmd)
    assert isinstance(err, ErrorEnvelope)
    assert err.category == "VALIDATION"
    assert err.code == "VALIDATION_ERROR"
    assert err.details["path"] == "command_id"

def test_missing_session_id():
    cmd = valid_cmd()
    cmd = cmd.__class__(
        command_id=cmd.command_id,
        session_id="",
        kind=cmd.kind,
        payload=cmd.payload,
        strict=cmd.strict,
        meta=cmd.meta,
    )
    err = validate_ingest_event_command(cmd)
    assert err and err.details["path"] == "session_id"

def test_wrong_type_command_id():
    cmd = valid_cmd()
    cmd = cmd.__class__(
        command_id=123,
        session_id=cmd.session_id,
        kind=cmd.kind,
        payload=cmd.payload,
        strict=cmd.strict,
        meta=cmd.meta,
    )
    err = validate_ingest_event_command(cmd)
    assert err and err.details["path"] == "command_id"

def test_wrong_type_payload():
    cmd = valid_cmd()
    cmd = cmd.__class__(
        command_id=cmd.command_id,
        session_id=cmd.session_id,
        kind=cmd.kind,
        payload="notapayload",
        strict=cmd.strict,
        meta=cmd.meta,
    )
    err = validate_ingest_event_command(cmd)
    assert err and err.details["path"] == "payload"

def test_empty_event_type():
    payload = IngestEventPayload(event_type="", data={"foo": 1})
    cmd = valid_cmd()
    cmd = cmd.__class__(
        command_id=cmd.command_id,
        session_id=cmd.session_id,
        kind=cmd.kind,
        payload=payload,
        strict=cmd.strict,
        meta=cmd.meta,
    )
    err = validate_ingest_event_command(cmd)
    assert err and err.details["path"] == "payload.event_type"

def test_data_not_dict():
    payload = IngestEventPayload(event_type="SOME_EVENT", data="notadict")
    cmd = valid_cmd()
    cmd = cmd.__class__(
        command_id=cmd.command_id,
        session_id=cmd.session_id,
        kind=cmd.kind,
        payload=payload,
        strict=cmd.strict,
        meta=cmd.meta,
    )
    err = validate_ingest_event_command(cmd)
    assert err and err.details["path"] == "payload.data"

def test_data_not_serializable():
    class NotSerializable:
        pass
    payload = IngestEventPayload(event_type="SOME_EVENT", data={"bad": NotSerializable()})
    cmd = valid_cmd()
    cmd = cmd.__class__(
        command_id=cmd.command_id,
        session_id=cmd.session_id,
        kind=cmd.kind,
        payload=payload,
        strict=cmd.strict,
        meta=cmd.meta,
    )
    err = validate_ingest_event_command(cmd)
    assert err and err.details["reason"] == "not JSON-serializable"

def test_data_with_callable():
    payload = IngestEventPayload(event_type="SOME_EVENT", data={"bad": lambda x: x})
    cmd = valid_cmd()
    cmd = cmd.__class__(
        command_id=cmd.command_id,
        session_id=cmd.session_id,
        kind=cmd.kind,
        payload=payload,
        strict=cmd.strict,
        meta=cmd.meta,
    )
    err = validate_ingest_event_command(cmd)
    assert err and "callable" in err.details["reason"]

def test_data_with_datetime():
    import datetime
    payload = IngestEventPayload(event_type="SOME_EVENT", data={"bad": datetime.datetime.now()})
    cmd = valid_cmd()
    cmd = cmd.__class__(
        command_id=cmd.command_id,
        session_id=cmd.session_id,
        kind=cmd.kind,
        payload=payload,
        strict=cmd.strict,
        meta=cmd.meta,
    )
    err = validate_ingest_event_command(cmd)
    assert err and "datetime" in err.details["reason"]

def test_client_sequence_wrong_type():
    payload = IngestEventPayload(event_type="SOME_EVENT", data={}, client_sequence="notint")
    cmd = valid_cmd()
    cmd = cmd.__class__(
        command_id=cmd.command_id,
        session_id=cmd.session_id,
        kind=cmd.kind,
        payload=payload,
        strict=cmd.strict,
        meta=cmd.meta,
    )
    err = validate_ingest_event_command(cmd)
    assert err and err.details["path"] == "payload.client_sequence"

def test_strict_wrong_type():
    cmd = valid_cmd()
    cmd = cmd.__class__(
        command_id=cmd.command_id,
        session_id=cmd.session_id,
        kind=cmd.kind,
        payload=cmd.payload,
        strict="notabool",
        meta=cmd.meta,
    )
    err = validate_ingest_event_command(cmd)
    assert err and err.details["path"] == "strict"

def test_meta_wrong_type():
    cmd = valid_cmd()
    cmd = cmd.__class__(
        command_id=cmd.command_id,
        session_id=cmd.session_id,
        kind=cmd.kind,
        payload=cmd.payload,
        strict=cmd.strict,
        meta="notadict",
    )
    err = validate_ingest_event_command(cmd)
    assert err and err.details["path"] == "meta"

def test_determinism():
    cmd = valid_cmd()
    result1 = validate_ingest_event_command(cmd)
    result2 = validate_ingest_event_command(cmd)
    assert result1 == result2
