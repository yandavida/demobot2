from typing import Optional
from dataclasses import dataclass

@dataclass(frozen=True)
class IngestOrderState:
    next_client_sequence: int

@dataclass(frozen=True)
class ErrorEnvelope:
    category: str
    code: str
    message: str
    details: dict
    error_count: int

def validate_ingest_event_ordering(state: IngestOrderState, cmd) -> Optional[ErrorEnvelope]:
    # cmd.payload.client_sequence may be None
    client_seq = getattr(getattr(cmd, 'payload', None), 'client_sequence', None)
    if client_seq is None:
        return None
    expected = state.next_client_sequence
    if client_seq != expected:
        return ErrorEnvelope(
            category="SEMANTIC",
            code="OUT_OF_ORDER",
            message="command violates ordering rules",
            details={
                "path": "payload.client_sequence",
                "reason": f"expected={expected}, got={client_seq}"
            },
            error_count=1
        )
    return None
