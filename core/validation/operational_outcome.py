from typing import Literal, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from .error_envelope import ErrorEnvelope

@dataclass(frozen=True)
class OperationalOutcome:
    command_id: str
    session_id: str
    status: Literal["ACCEPTED", "IDEMPOTENT_REPLAY", "REJECTED"]
    error: Optional[ErrorEnvelope]
    state_hash: Optional[str]
    diagnostics: Optional[Dict[str, Any]] = None

def map_classification_to_outcome(
    classification: str,
    identity: Tuple[str, str],
    state_hash: Optional[str],
    diagnostics: Optional[Dict[str, Any]] = None
) -> OperationalOutcome:
    session_id, command_id = identity
    if classification == "NEW":
        return OperationalOutcome(
            command_id=command_id,
            session_id=session_id,
            status="ACCEPTED",
            error=None,
            state_hash=state_hash,
            diagnostics=diagnostics,
        )
    if classification == "IDEMPOTENT_REPLAY":
        return OperationalOutcome(
            command_id=command_id,
            session_id=session_id,
            status="IDEMPOTENT_REPLAY",
            error=None,
            state_hash=state_hash,
            diagnostics=diagnostics,
        )
    if classification == "CONFLICT":
        err = ErrorEnvelope(
            category="CONFLICT",
            code="IDEMPOTENCY_CONFLICT",
            message="command conflicts with previous execution",
            details={"path": "", "reason": "conflict with previous fingerprint"},
            error_count=1,
        )
        return OperationalOutcome(
            command_id=command_id,
            session_id=session_id,
            status="REJECTED",
            error=err,
            state_hash=state_hash,
            diagnostics=diagnostics,
        )
    raise ValueError(f"Unknown classification: {classification}")
