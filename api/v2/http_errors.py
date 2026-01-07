from dataclasses import asdict, is_dataclass
from typing import Any, Dict, NoReturn
from fastapi import HTTPException


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
