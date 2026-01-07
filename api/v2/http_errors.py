from dataclasses import asdict, is_dataclass
from typing import Any, Dict, NoReturn
from fastapi import HTTPException

# Use the canonical ErrorEnvelope from core as the single source of truth
from core.validation.error_envelope import ErrorEnvelope


def envelope_to_detail(env: Any) -> Dict[str, Any]:
    """Normalize an error envelope (dataclass / object / dict) to a plain dict.

    Expected output keys: category, code, message, details (and others if present).
    """
    if env is None:
        return {}
    if isinstance(env, dict):
        return env
    if is_dataclass(env):
        return asdict(env)
    # Fallback: try attribute extraction
    return {
        "category": getattr(env, "category", None),
        "code": getattr(env, "code", None),
        "message": getattr(env, "message", None),
        "details": getattr(env, "details", {}) or {},
    }


def raise_http(env: Any, status_code: int) -> NoReturn:
    """Raise a FastAPI HTTPException with the canonical envelope dict as `detail`.

    Use this helper to ensure all API errors use `detail=<envelope dict>`.
    """
    raise HTTPException(status_code=status_code, detail=envelope_to_detail(env))


def bad_request(code: str, message: str, details: Dict[str, Any] | None = None) -> NoReturn:
    env = ErrorEnvelope(category="VALIDATION", code=code, message=message, details=details or {})
    raise_http(env, 400)


def not_found(code: str, message: str, details: Dict[str, Any] | None = None) -> NoReturn:
    env = ErrorEnvelope(category="NOT_FOUND", code=code, message=message, details=details or {})
    raise_http(env, 404)


def unprocessable(code: str, message: str, details: Dict[str, Any] | None = None) -> NoReturn:
    env = ErrorEnvelope(category="VALIDATION", code=code, message=message, details=details or {})
    raise_http(env, 422)


def internal_error(message: str = "Internal Server Error") -> NoReturn:
    env = ErrorEnvelope(category="SERVER", code="internal_error", message=message, details={})
    raise_http(env, 500)
