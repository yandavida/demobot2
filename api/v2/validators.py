
from __future__ import annotations
from typing import Any, Dict
from fastapi import HTTPException

def validate_compute_payload(payload: Dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail={"detail": "payload must be an object"})

    kind = payload.get("kind")
    params = payload.get("params")

    if kind not in {"SNAPSHOT", "PORTFOLIO_RISK", "SCENARIO_GRID"}:
        raise HTTPException(status_code=400, detail={"detail": "payload.kind must be one of: SNAPSHOT, PORTFOLIO_RISK, SCENARIO_GRID"})

    if not isinstance(params, dict) or len(params) == 0:
        raise HTTPException(status_code=400, detail={"detail": "payload.params must be a non-empty object"})

def validate_quote_payload(payload: Dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail={"detail": "payload must be an object"})
    if len(payload) == 0:
        raise HTTPException(status_code=400, detail={"detail": "payload must not be empty"})
