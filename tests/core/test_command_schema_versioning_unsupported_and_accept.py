from core.validation.command_registry import validate_command_dict
from core.validation.operational_outcome import ErrorEnvelope


def make_cmd(kind: str, sv: int):
    return {"kind": kind, "schema_version": sv, "command_id": "c", "session_id": "s", "client_sequence": 1, "payload": {}}


def test_unsupported_schema_version_rejected():
    cmd = make_cmd("INGEST_QUOTE", 999)
    err = validate_command_dict(cmd)
    assert isinstance(err, ErrorEnvelope)
    assert err.code == "UNSUPPORTED_SCHEMA_VERSION"


def test_supported_schema_version_accepted():
    cmd = make_cmd("INGEST_QUOTE", 1)
    err = validate_command_dict(cmd)
    assert err is None
