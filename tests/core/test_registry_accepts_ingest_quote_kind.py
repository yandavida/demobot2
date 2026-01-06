from core.validation.command_registry import validate_command_kind
from core.validation.operational_outcome import ErrorEnvelope


def test_registry_accepts_ingest_quote_kind():
    assert validate_command_kind("INGEST_QUOTE") is None


def test_registry_unknown_kind_rejected():
    err = validate_command_kind("NO_SUCH_KIND")
    assert isinstance(err, ErrorEnvelope)
    assert err.category == "VALIDATION"
    assert err.code == "UNKNOWN_COMMAND_KIND"
