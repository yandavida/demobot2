from typing import Literal, Dict

from .error_envelope import ErrorEnvelope


Category = Literal["VALIDATION", "SEMANTIC", "CONFLICT"]

Code = Literal[
    "VALIDATION_ERROR",
    "UNKNOWN_COMMAND_KIND",
    "OUT_OF_ORDER",
    "IDEMPOTENCY_CONFLICT",
]


# Stable message mapping per code (no dynamic data in message)
_MESSAGE_MAP: dict[str, str] = {
    "VALIDATION_ERROR": "validation error",
    "UNKNOWN_COMMAND_KIND": "unsupported command kind",
    "OUT_OF_ORDER": "command violates ordering rules",
    "IDEMPOTENCY_CONFLICT": "command conflicts with previous execution",
}


def _category_for_code(code: str) -> Category:
    if code in {"VALIDATION_ERROR", "UNKNOWN_COMMAND_KIND"}:
        return "VALIDATION"
    if code == "OUT_OF_ORDER":
        return "SEMANTIC"
    if code == "IDEMPOTENCY_CONFLICT":
        return "CONFLICT"
    # fallback
    return "VALIDATION"


def make_error(code: Code, details: Dict[str, str]) -> ErrorEnvelope:
    cat = _category_for_code(code)
    msg = _MESSAGE_MAP.get(code, "error")
    return ErrorEnvelope(category=cat, code=code, message=msg, details=details, error_count=1)
