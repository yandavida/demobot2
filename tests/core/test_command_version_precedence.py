from core.validation.command_registry import validate_command_dict
from core.validation.operational_outcome import ErrorEnvelope


def test_version_check_happens_before_payload_validation():
    # Create a command with unsupported schema_version and an otherwise invalid payload
    cmd = {
        "kind": "INGEST_QUOTE",
        "schema_version": 999,  # unsupported
        "command_id": "c",
        "session_id": "s",
        "client_sequence": 1,
        "payload": {"symbol": "", "price": -1},
    }
    err = validate_command_dict(cmd)
    # Expect the versioning error, not a payload field error
    assert isinstance(err, ErrorEnvelope)
    assert err.code == "UNSUPPORTED_SCHEMA_VERSION"
