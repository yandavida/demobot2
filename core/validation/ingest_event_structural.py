from typing import Any, Dict, Literal, Optional, Union
from dataclasses import dataclass
import json
from .error_envelope import ErrorEnvelope
from .error_taxonomy import make_error

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
# Reuse canonical ErrorEnvelope from core.validation.error_envelope

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
        return make_error("VALIDATION_ERROR", details={"path": "", "reason": "type"})
    # command_id
    if not isinstance(cmd.command_id, str) or not cmd.command_id:
        return make_error("VALIDATION_ERROR", details={"path": "command_id", "reason": "required/non-empty str"})
    # session_id
    if not isinstance(cmd.session_id, str) or not cmd.session_id:
        return make_error("VALIDATION_ERROR", details={"path": "session_id", "reason": "required/non-empty str"})
    # kind
    if cmd.kind != "INGEST_EVENT":
        return make_error("VALIDATION_ERROR", details={"path": "kind", "reason": "must be 'INGEST_EVENT'"})
    # payload
    if not isinstance(cmd.payload, IngestEventPayload):
        return make_error("VALIDATION_ERROR", details={"path": "payload", "reason": "type"})
    # event_type
    if not isinstance(cmd.payload.event_type, str) or not cmd.payload.event_type:
        return make_error("VALIDATION_ERROR", details={"path": "payload.event_type", "reason": "required/non-empty str"})
    # data
    if not isinstance(cmd.payload.data, dict):
        return make_error("VALIDATION_ERROR", details={"path": "payload.data", "reason": "type"})
    # Blacklist: no callables, datetime, generators, etc. (deterministic traversal)
    for k in sorted(cmd.payload.data.keys()):
        v = cmd.payload.data[k]
        if callable(v):
            return make_error("VALIDATION_ERROR", details={"path": "payload.data", "reason": "contains callable"})
        if hasattr(v, "__iter__") and not isinstance(v, (str, bytes, dict, list, tuple, set)):
            return make_error("VALIDATION_ERROR", details={"path": "payload.data", "reason": "contains generator/non-serializable"})
        if type(v).__name__ in ("datetime", "date", "time"):
            return make_error("VALIDATION_ERROR", details={"path": "payload.data", "reason": "contains datetime"})
    if not is_json_serializable(cmd.payload.data):
        return make_error("VALIDATION_ERROR", details={"path": "payload.data", "reason": "not JSON-serializable"})
    # client_sequence
    if cmd.payload.client_sequence is not None and not isinstance(cmd.payload.client_sequence, int):
        return make_error("VALIDATION_ERROR", details={"path": "payload.client_sequence", "reason": "type"})
    # strict
    if not isinstance(cmd.strict, bool):
        return make_error("VALIDATION_ERROR", details={"path": "strict", "reason": "type"})
    # meta
    if cmd.meta is not None and not isinstance(cmd.meta, dict):
        return make_error("VALIDATION_ERROR", details={"path": "meta", "reason": "type"})
    return None
