from typing import Any, Dict, Literal, Optional, Union
from dataclasses import dataclass
import json

# --- Command Spec ---
@dataclass(frozen=True)
class IngestEventPayload:
    event_type: str
    data: Dict[str, Any]
    client_sequence: Optional[int] = None

@dataclass(frozen=True)
class IngestEventCommand:
    command_id: str
    session_id: str
    kind: Literal["INGEST_EVENT"]
    payload: IngestEventPayload
    strict: bool
    meta: Optional[Dict[str, Any]] = None

# --- Error Envelope ---
@dataclass(frozen=True)
class ErrorEnvelope:
    category: str
    code: str
    message: str
    details: Dict[str, Any]

# --- Validation Logic ---
def is_json_serializable(obj: Any) -> bool:
    try:
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return True
    except Exception:
        return False

def validate_ingest_event_command(cmd: Any) -> Union[None, ErrorEnvelope]:
    # Check type
    if not isinstance(cmd, IngestEventCommand):
        return ErrorEnvelope(
            category="VALIDATION",
            code="VALIDATION_ERROR",
            message="Command must be IngestEventCommand",
            details={"path": "", "reason": "type"},
        )
    # command_id
    if not isinstance(cmd.command_id, str) or not cmd.command_id:
        return ErrorEnvelope(
            category="VALIDATION",
            code="VALIDATION_ERROR",
            message="command_id must be non-empty str",
            details={"path": "command_id", "reason": "required/non-empty str"},
        )
    # session_id
    if not isinstance(cmd.session_id, str) or not cmd.session_id:
        return ErrorEnvelope(
            category="VALIDATION",
            code="VALIDATION_ERROR",
            message="session_id must be non-empty str",
            details={"path": "session_id", "reason": "required/non-empty str"},
        )
    # kind
    if cmd.kind != "INGEST_EVENT":
        return ErrorEnvelope(
            category="VALIDATION",
            code="VALIDATION_ERROR",
            message="kind must be 'INGEST_EVENT'",
            details={"path": "kind", "reason": "must be 'INGEST_EVENT'"},
        )
    # payload
    if not isinstance(cmd.payload, IngestEventPayload):
        return ErrorEnvelope(
            category="VALIDATION",
            code="VALIDATION_ERROR",
            message="payload must be IngestEventPayload",
            details={"path": "payload", "reason": "type"},
        )
    # event_type
    if not isinstance(cmd.payload.event_type, str) or not cmd.payload.event_type:
        return ErrorEnvelope(
            category="VALIDATION",
            code="VALIDATION_ERROR",
            message="event_type must be non-empty str",
            details={"path": "payload.event_type", "reason": "required/non-empty str"},
        )
    # data
    if not isinstance(cmd.payload.data, dict):
        return ErrorEnvelope(
            category="VALIDATION",
            code="VALIDATION_ERROR",
            message="data must be dict",
            details={"path": "payload.data", "reason": "type"},
        )
    # Blacklist: no callables, datetime, generators, etc. (deterministic traversal)
    for k in sorted(cmd.payload.data.keys()):
        v = cmd.payload.data[k]
        if callable(v):
            return ErrorEnvelope(
                category="VALIDATION",
                code="VALIDATION_ERROR",
                message="data must not contain callables",
                details={"path": "payload.data", "reason": "contains callable"},
            )
        if hasattr(v, "__iter__") and not isinstance(v, (str, bytes, dict, list, tuple, set)):
            return ErrorEnvelope(
                category="VALIDATION",
                code="VALIDATION_ERROR",
                message="data must not contain generators or non-serializables",
                details={"path": "payload.data", "reason": "contains generator/non-serializable"},
            )
        if type(v).__name__ in ("datetime", "date", "time"):
            return ErrorEnvelope(
                category="VALIDATION",
                code="VALIDATION_ERROR",
                message="data must not contain datetime",
                details={"path": "payload.data", "reason": "contains datetime"},
            )
    if not is_json_serializable(cmd.payload.data):
        return ErrorEnvelope(
            category="VALIDATION",
            code="VALIDATION_ERROR",
            message="data must be JSON-serializable",
            details={"path": "payload.data", "reason": "not JSON-serializable"},
        )
    # client_sequence
    if cmd.payload.client_sequence is not None and not isinstance(cmd.payload.client_sequence, int):
        return ErrorEnvelope(
            category="VALIDATION",
            code="VALIDATION_ERROR",
            message="client_sequence must be int or None",
            details={"path": "payload.client_sequence", "reason": "type"},
        )
    # strict
    if not isinstance(cmd.strict, bool):
        return ErrorEnvelope(
            category="VALIDATION",
            code="VALIDATION_ERROR",
            message="strict must be bool",
            details={"path": "strict", "reason": "type"},
        )
    # meta
    if cmd.meta is not None and not isinstance(cmd.meta, dict):
        return ErrorEnvelope(
            category="VALIDATION",
            code="VALIDATION_ERROR",
            message="meta must be dict or None",
            details={"path": "meta", "reason": "type"},
        )
    return None
