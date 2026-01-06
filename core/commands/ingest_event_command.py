from dataclasses import dataclass
from typing import Literal, Optional, Dict


@dataclass(frozen=True)
class IngestEventPayload:
    event_type: str
    data: Dict[str, object]
    client_sequence: Optional[int] = None


@dataclass(frozen=True)
class IngestEventCommand:
    command_id: str
    session_id: str
    payload: IngestEventPayload
    kind: Literal["INGEST_EVENT"] = "INGEST_EVENT"
    strict: bool = True
    meta: Optional[Dict[str, object]] = None
