from typing import List
from fastapi import HTTPException
from api.v2.read_models_schemas import (
    EventViewItem, EventsListResponse, SnapshotMetadataResponse,
    ComputeRequestViewItem, ComputeRequestsListResponse
)
from api.v2.service import v2_service

def list_events(session_id: str, *, limit: int, include_payload: bool) -> EventsListResponse:
    if not (1 <= limit <= 500):
        raise HTTPException(status_code=400, detail="limit must be between 1 and 500")
    # session_exists rule: any event or snapshot
    if not v2_service.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    events = v2_service.event_store.list(session_id)
    # order: ts, event_id
    events = sorted(events, key=lambda e: (e.ts, e.event_id))[:limit]
    items: List[EventViewItem] = []
    for e in events:
        item = EventViewItem(
            event_id=e.event_id,
            ts=e.ts,
            type=e.type,
            payload_hash=e.payload_hash,
            state_version=None,  # can be extended if needed
            payload=e.payload if include_payload else None
        )
        items.append(item)
    return EventsListResponse(session_id=session_id, items=items)

def get_snapshot_metadata(session_id: str) -> SnapshotMetadataResponse:
    snap = v2_service.snapshot_store.latest(session_id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return SnapshotMetadataResponse(
        session_id=snap.session_id,
        state_version=snap.version,
        state_hash=snap.state_hash,
        created_at=snap.created_at
    )

def list_compute_requests(session_id: str, *, limit: int, include_params: bool) -> ComputeRequestsListResponse:
    if not (1 <= limit <= 500):
        raise HTTPException(status_code=400, detail="limit must be between 1 and 500")
    if not v2_service.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    events = v2_service.event_store.list(session_id)
    compute_events = [e for e in events if e.type == "COMPUTE_REQUESTED"]
    compute_events = sorted(compute_events, key=lambda e: (e.ts, e.event_id))[:limit]
    items: List[ComputeRequestViewItem] = []
    for e in compute_events:
        payload = e.payload
        item = ComputeRequestViewItem(
            event_id=e.event_id,
            ts=e.ts,
            kind=payload["kind"],
            params_hash=e.payload_hash,
            params=payload["params"] if include_params else None
        )
        items.append(item)
    return ComputeRequestsListResponse(session_id=session_id, items=items)
