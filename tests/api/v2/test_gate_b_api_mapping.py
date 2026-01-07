import pytest

from api.v2.gate_b import (
    parse_request,
    map_api_to_command,
    format_success,
    format_error_envelope,
    ErrorEnvelope,
)


def test_missing_schema_version_precedence():
    req = {"kind": "INGEST_QUOTE", "payload": {"symbol": "AAPL", "price": 100}}
    mapped, err = parse_request(req)
    assert mapped is None
    assert err is not None
    assert err.code == "missing_schema_version"


def test_unsupported_schema_version():
    req = {"schema_version": "2.0", "kind": "INGEST_QUOTE", "payload": {"symbol": "AAPL", "price": 100}}
    mapped, err = parse_request(req)
    assert mapped is None
    assert err.code == "unsupported_schema_version"


def test_unknown_kind_rejected():
    req = {"schema_version": "1.0", "kind": "UNKNOWN", "payload": {"symbol": "AAPL", "price": 100}}
    mapped, err = parse_request(req)
    assert mapped is None
    assert err.code == "unknown_kind"


def test_strict_validation_rejects_invalid_payload():
    req = {"schema_version": "1.0", "kind": "INGEST_QUOTE", "payload": {"symbol": "AAPL"}, "validation_mode": "strict"}
    with pytest.raises(ValueError) as exc:
        map_api_to_command(req)
    err = exc.value.args[0]
    assert isinstance(err, dict)
    assert err["code"] == "invalid_payload_price"


def test_lenient_validation_embeds_warnings():
    req = {"schema_version": "1.0", "kind": "INGEST_QUOTE", "payload": {"symbol": "AAPL"}, "validation_mode": "lenient"}
    cmd = map_api_to_command(req)
    assert "warnings" in cmd
    assert len(cmd["warnings"]) == 1
    assert cmd["warnings"][0]["code"] == "invalid_payload_price"


def test_legality_failure_precedes_command_execution():
    req = {"schema_version": "1.0", "kind": "INGEST_QUOTE", "payload": {"symbol": "aa", "price": 100}}
    with pytest.raises(ValueError) as exc:
        map_api_to_command(req)
    err = exc.value.args[0]
    assert err["code"] == "symbol_not_uppercase"


def test_formatting_envelopes():
    res = format_success({"id": "abc"})
    assert res["status"] == "ok"
    e = ErrorEnvelope("client", "x", "m").to_dict()
    out = format_error_envelope(e)
    assert "error" in out
