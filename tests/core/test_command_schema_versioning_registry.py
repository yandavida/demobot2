from core.validation.command_registry import validate_command_dict
from core.validation.operational_outcome import ErrorEnvelope


def make_base_command(kind: str):
    return {"kind": kind, "command_id": "c", "session_id": "s", "client_sequence": 1, "payload": {}}


def test_missing_schema_version_rejected_ingest_quote():
    cmd = make_base_command("INGEST_QUOTE")
    # intentionally omit schema_version
    err = validate_command_dict(cmd)
    assert isinstance(err, ErrorEnvelope)
    assert err.code == "MISSING_SCHEMA_VERSION"


def test_missing_schema_version_rejected_ingest_event():
    cmd = make_base_command("INGEST_EVENT")
    err = validate_command_dict(cmd)
    assert isinstance(err, ErrorEnvelope)
    assert err.code == "MISSING_SCHEMA_VERSION"
