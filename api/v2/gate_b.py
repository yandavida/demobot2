from typing import Any, Dict, Optional, Tuple

# Canonical API contract shapes for Gate B
# Request shape: {"kind": str, "schema_version": str, "payload": dict, "validation_mode": "strict"|"lenient" (optional)}
# Response shapes:
#  - Success: {"status":"ok","result": {...}}
#  - Validation/Legality Failure (strict): ErrorEnvelope -> {"error": {"category":...,"code":...,"message":...,"details":...}}
#  - Lenient: {"status":"ok","result": {...}, "warnings": [...]}


class ErrorEnvelope:
    def __init__(self, category: str, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.category = category
        self.code = code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


# Deterministic validators and mapping logic. No clock/random/envs.
SUPPORTED_KINDS = {"INGEST_QUOTE": "1.0"}
SUPPORTED_SCHEMA_VERSIONS = {"1.0"}
VALIDATION_MODES = {"strict", "lenient"}


def parse_request(req: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[ErrorEnvelope]]:
    # Precedence: schema_version must be present and supported before deeper validation
    if "schema_version" not in req:
        return None, ErrorEnvelope("client", "missing_schema_version", "`schema_version` is required", {})
    schema_version = req.get("schema_version")
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        return None, ErrorEnvelope("client", "unsupported_schema_version", f"schema_version {schema_version} is unsupported", {"supported": sorted(list(SUPPORTED_SCHEMA_VERSIONS))})

    # kind
    kind = req.get("kind")
    if not kind or not isinstance(kind, str):
        return None, ErrorEnvelope("client", "missing_kind", "`kind` is required and must be a string", {})
    if kind not in SUPPORTED_KINDS:
        return None, ErrorEnvelope("client", "unknown_kind", f"Unknown kind: {kind}", {})

    # validation_mode
    validation_mode = req.get("validation_mode", "strict")
    if validation_mode not in VALIDATION_MODES:
        return None, ErrorEnvelope("client", "invalid_validation_mode", f"validation_mode {validation_mode} invalid", {"allowed": sorted(list(VALIDATION_MODES))})

    # payload must be present
    payload = req.get("payload")
    if payload is None or not isinstance(payload, dict):
        return None, ErrorEnvelope("client", "missing_or_invalid_payload", "`payload` must be an object", {})

    mapped = {
        "kind": kind,
        "schema_version": schema_version,
        "payload": payload,
        "validation_mode": validation_mode,
    }
    return mapped, None


def validate_payload(kind: str, payload: Dict[str, Any]) -> Tuple[bool, Optional[ErrorEnvelope]]:
    # Minimal deterministic payload validation per kind and schema_version
    # For INGEST_QUOTE expect keys: symbol (str), price (number)
    if kind == "INGEST_QUOTE":
        if "symbol" not in payload or not isinstance(payload.get("symbol"), str):
            return False, ErrorEnvelope("validation", "invalid_payload_symbol", "`symbol` missing or invalid", {})
        if "price" not in payload or not (isinstance(payload.get("price"), (int, float))):
            return False, ErrorEnvelope("validation", "invalid_payload_price", "`price` missing or invalid", {})
        return True, None
    # default: accept (but in practice unknown kinds rejected earlier)
    return True, None


def apply_workflow_legality(kind: str, payload: Dict[str, Any]) -> Tuple[bool, Optional[ErrorEnvelope]]:
    # Simple deterministic legality check: symbol must be uppercase and length <= 8
    symbol = payload.get("symbol")
    if symbol and isinstance(symbol, str):
        if symbol.upper() != symbol:
            return False, ErrorEnvelope("legality", "symbol_not_uppercase", "symbol must be uppercase", {"symbol": symbol})
        if len(symbol) > 8:
            return False, ErrorEnvelope("legality", "symbol_too_long", "symbol length must be <= 8", {"symbol": symbol})
    return True, None


def map_api_to_command(req: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map an incoming HTTP JSON body into a typed Gate B command or raise an ErrorEnvelope (as exception) for API-layer errors.
    This function enforces precedence: schema_version -> parse -> validate -> legality.
    Validation mode affects whether validation failures return errors (strict) or warnings (lenient).
    """
    mapped, err = parse_request(req)
    if err:
        raise ValueError(err.to_dict())

    kind = mapped["kind"]
    validation_mode = mapped["validation_mode"]
    payload = mapped["payload"]

    valid, v_err = validate_payload(kind, payload)
    if not valid:
        if validation_mode == "strict":
            raise ValueError(v_err.to_dict())
        # lenient: continue but record warning
        warnings = [v_err.to_dict()]
    else:
        warnings = []

    legal, l_err = apply_workflow_legality(kind, payload)
    if not legal:
        # legality failures are considered API-layer deterministic failures and return ErrorEnvelope in both modes
        raise ValueError(l_err.to_dict())

    # On success (or lenient with warnings), return canonical command dict
    command = {
        "command_kind": kind,
        "schema_version": mapped["schema_version"],
        "payload": payload,
        "warnings": warnings,
    }
    return command


def format_success(result: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "ok", "result": result}


def format_error_envelope(envelope: Dict[str, Any]) -> Dict[str, Any]:
    return {"error": envelope}
