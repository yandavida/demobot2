import math
from core.commands.ingest_quote_command import IngestQuoteCommand, IngestQuotePayload
from core.validation.error_taxonomy import make_error
from core.validation.error_envelope import ErrorEnvelope


def validate_payload_contract(cmd) -> ErrorEnvelope | None:
    # Minimal contract-level checks (tests only)
    if not isinstance(cmd, IngestQuoteCommand):
        return make_error("VALIDATION_ERROR", details={"path": "", "reason": "type"})
    p = cmd.payload
    if not isinstance(p.symbol, str) or not p.symbol:
        return make_error("VALIDATION_ERROR", details={"path": "payload.symbol", "reason": "required/non-empty str"})
    if not isinstance(p.price, float) and not isinstance(p.price, int):
        return make_error("VALIDATION_ERROR", details={"path": "payload.price", "reason": "type"})
    if not math.isfinite(p.price):
        return make_error("VALIDATION_ERROR", details={"path": "payload.price", "reason": "non-finite"})
    if p.price <= 0:
        return make_error("VALIDATION_ERROR", details={"path": "payload.price", "reason": "must be > 0"})
    if not isinstance(p.currency, str) or not p.currency:
        return make_error("VALIDATION_ERROR", details={"path": "payload.currency", "reason": "required/non-empty str"})
    return None


def test_empty_symbol_rejected():
    cmd = IngestQuoteCommand(schema_version=1, command_id="c1", session_id="s1", client_sequence=1,
                             payload=IngestQuotePayload(symbol="", price=1.0, currency="USD"))
    err = validate_payload_contract(cmd)
    assert isinstance(err, ErrorEnvelope)
    assert err.code == "VALIDATION_ERROR"


def test_non_finite_price_rejected():
    cmd = IngestQuoteCommand(schema_version=1, command_id="c2", session_id="s2", client_sequence=1,
                             payload=IngestQuotePayload(symbol="S", price=float('nan'), currency="USD"))
    err = validate_payload_contract(cmd)
    assert isinstance(err, ErrorEnvelope)
    assert err.code == "VALIDATION_ERROR"


def test_price_le_zero_rejected():
    cmd = IngestQuoteCommand(schema_version=1, command_id="c3", session_id="s3", client_sequence=1,
                             payload=IngestQuotePayload(symbol="S", price=0.0, currency="USD"))
    err = validate_payload_contract(cmd)
    assert isinstance(err, ErrorEnvelope)
    assert err.code == "VALIDATION_ERROR"


def test_valid_payload_accepted():
    cmd = IngestQuoteCommand(schema_version=1, command_id="c4", session_id="s4", client_sequence=1,
                             payload=IngestQuotePayload(symbol="S", price=1.23, currency="USD"))
    err = validate_payload_contract(cmd)
    assert err is None
