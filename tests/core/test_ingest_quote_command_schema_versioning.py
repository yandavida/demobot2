from types import SimpleNamespace
from core.commands.ingest_quote_command import IngestQuoteCommand, IngestQuotePayload
from core.validation.error_taxonomy import make_error
from core.validation.error_envelope import ErrorEnvelope


def validate_schema_version(obj) -> ErrorEnvelope | None:
    # Minimal, contract-level checks used by tests only
    if not hasattr(obj, "schema_version"):
        return make_error("VALIDATION_ERROR", details={"path": "schema_version", "reason": "missing"})
    sv = getattr(obj, "schema_version")
    if not isinstance(sv, int):
        return make_error("VALIDATION_ERROR", details={"path": "schema_version", "reason": "type"})
    # unsupported versions: only 1 supported for now
    if sv != 1:
        return make_error("VALIDATION_ERROR", details={"path": "schema_version", "reason": "unsupported"})
    return None


def test_missing_schema_version_rejected():
    obj = SimpleNamespace()  # no schema_version attribute
    err = validate_schema_version(obj)
    assert isinstance(err, ErrorEnvelope)
    assert err.code == "VALIDATION_ERROR"


def test_unsupported_schema_version_rejected():
    cmd = IngestQuoteCommand(schema_version=2, command_id="c1", session_id="s1", client_sequence=1,
                             payload=IngestQuotePayload(symbol="X", price=1.0, currency="USD"))
    err = validate_schema_version(cmd)
    assert isinstance(err, ErrorEnvelope)
    assert err.code == "VALIDATION_ERROR"


def test_supported_schema_version_accepted():
    cmd = IngestQuoteCommand(schema_version=1, command_id="c2", session_id="s2", client_sequence=1,
                             payload=IngestQuotePayload(symbol="X", price=1.0, currency="USD"))
    err = validate_schema_version(cmd)
    assert err is None
