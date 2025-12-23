from __future__ import annotations
from typing import Any, Dict
from fastapi import HTTPException

def validate_quote_payload(payload: Dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail={"detail": "payload must be an object"})
    if len(payload) == 0:
        raise HTTPException(status_code=400, detail={"detail": "payload must not be empty"})
