from typing import Optional
from dataclasses import dataclass
from .error_envelope import ErrorEnvelope
from .error_taxonomy import make_error


@dataclass(frozen=True)
class IngestOrderState:
    next_client_sequence: int


def validate_ingest_event_ordering(state: IngestOrderState, cmd) -> Optional[ErrorEnvelope]:
    # cmd.payload.client_sequence may be None
    client_seq = getattr(getattr(cmd, 'payload', None), 'client_sequence', None)
    if client_seq is None:
        return None
    expected = state.next_client_sequence
    if client_seq != expected:
        return make_error("OUT_OF_ORDER", details={
            "path": "payload.client_sequence",
            "reason": f"expected={expected}, got={client_seq}"
        })
    return None
