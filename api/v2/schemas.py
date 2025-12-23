from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel
from core.v2.models import EventType

class CreateSessionResponse(BaseModel):
    session_id: str

class IngestEventRequest(BaseModel):
    event_id: Optional[str] = None
    ts: Optional[datetime] = None
    type: EventType
    payload: dict[str, Any]

class IngestEventResponse(BaseModel):
    session_id: str
    state_version: int
    applied: bool
    correlation_id: Optional[str] = None

class SnapshotResponse(BaseModel):
    session_id: str
    version: int
    state_hash: str
    data: dict[str, Any]
    correlation_id: Optional[str] = None
