
from __future__ import annotations
from typing import Any, Dict
from fastapi import HTTPException

from api.v2.gate_b import ErrorEnvelope

def validate_compute_payload(payload: Dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail={"detail": "payload must be an object"})

    kind = payload.get("kind")
    params = payload.get("params")

    if kind not in {"SNAPSHOT", "PORTFOLIO_RISK", "SCENARIO_GRID"}:
        raise HTTPException(status_code=400, detail={"detail": "payload.kind must be one of: SNAPSHOT, PORTFOLIO_RISK, SCENARIO_GRID"})

    if not isinstance(params, dict) or len(params) == 0:
        raise HTTPException(status_code=400, detail={"detail": "payload.params must be a non-empty object"})

    # For SNAPSHOT compute requests, require a canonical market_snapshot_id (string)
    if kind == "SNAPSHOT":
        msid = params.get("market_snapshot_id")
        if not isinstance(msid, str) or len(msid) == 0:
            env = ErrorEnvelope("validation", "missing_market_snapshot_id", "`market_snapshot_id` is required in payload.params for SNAPSHOT", {})
            raise HTTPException(status_code=400, detail=env.to_dict())
        # optional: basic format check (sha256 hex length)
        if not (len(msid) == 64 and all(c in "0123456789abcdef" for c in msid.lower())):
            env = ErrorEnvelope("validation", "invalid_market_snapshot_id", "`market_snapshot_id` format invalid", {"value": msid})
            raise HTTPException(status_code=400, detail=env.to_dict())

def validate_quote_payload(payload: Dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail={"detail": "payload must be an object"})
    if len(payload) == 0:
        raise HTTPException(status_code=400, detail={"detail": "payload must not be empty"})
