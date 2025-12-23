from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class EventViewItem(BaseModel):
    event_id: str
    ts: datetime
    type: str
    payload_hash: str
    state_version: Optional[int] = None
    payload: Optional[Dict[str, Any]] = None

class EventsListResponse(BaseModel):
    session_id: str
    items: List[EventViewItem]

class SnapshotMetadataResponse(BaseModel):
    session_id: str
    state_version: int
    state_hash: str
    created_at: datetime

class ComputeRequestViewItem(BaseModel):
    event_id: str
    ts: datetime
    kind: str
    params_hash: str
    params: Optional[Dict[str, Any]] = None

class ComputeRequestsListResponse(BaseModel):
    session_id: str
    items: List[ComputeRequestViewItem]
