from core.validation.command_registry import validate_command_kind
from core.validation.operational_outcome import ErrorEnvelope


def test_known_kind_returns_none():
    # Canonical kinds on this Gate B PR must be accepted
    assert validate_command_kind("INGEST_EVENT") is None
    assert validate_command_kind("SNAPSHOT_REQUEST") is None

    # Legacy / non-canonical kind must be rejected under Gate B
    err = validate_command_kind("SNAPSHOT")
    assert err is not None
    assert err.code == "UNKNOWN_COMMAND_KIND"


def test_unknown_kind_returns_error_envelope():
    err = validate_command_kind("NO_SUCH_KIND")
    assert isinstance(err, ErrorEnvelope)
    assert err.category == "VALIDATION"
    assert err.code == "UNKNOWN_COMMAND_KIND"
    assert err.message == "unsupported command kind"
    assert err.details == {"path": "kind", "reason": "unknown kind: NO_SUCH_KIND"}
    assert err.error_count == 1
