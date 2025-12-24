from typing import Any, Dict, List

from fastapi import HTTPException

from api.v2.read_models_schemas import (
    EventViewItem,
    EventsListResponse,
    SnapshotMetadataResponse,
    ComputeRequestViewItem,
    ComputeRequestsListResponse,
)
from api.v2.service import v2_service


def _etype_str(t: Any) -> str:
    return t.value if hasattr(t, "value") else str(t)


def _payload_dict(p: Any) -> Dict[str, Any]:
    return p if isinstance(p, dict) else {}


def list_events(session_id: str, *, limit: int, include_payload: bool) -> EventsListResponse:
    if not (1 <= limit <= 500):
        raise HTTPException(status_code=400, detail="limit must be between 1 and 500")
    if v2_service.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    events = v2_service.event_store.list(session_id) if hasattr(v2_service, "event_store") else []
    events = sorted(events, key=lambda e: (e.ts, e.event_id))[:limit] if events else []
    items: List[EventViewItem] = []
    for e in events:
        kwargs = dict(
            event_id=e.event_id,
            ts=e.ts,
            type=_etype_str(e.type),
            payload_hash=e.payload_hash,
            state_version=None,
            payload=_payload_dict(e.payload) if include_payload else None
        )
        items.append(EventViewItem(**kwargs))
    return EventsListResponse(session_id=session_id, items=items)


def get_snapshot_metadata(session_id: str) -> SnapshotMetadataResponse:
    snap = v2_service.snapshot_store.latest(session_id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return SnapshotMetadataResponse(
        session_id=snap.session_id,
        state_version=snap.version,
        state_hash=snap.state_hash,
        created_at=getattr(snap, "created_at", None) or getattr(snap, "ts", None),
    )


def list_compute_requests(session_id: str, *, limit: int, include_params: bool) -> ComputeRequestsListResponse:
    if not (1 <= limit <= 500):
        raise HTTPException(status_code=400, detail="limit must be between 1 and 500")
    if v2_service.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    events = v2_service.event_store.list(session_id) if hasattr(v2_service, "event_store") else []
    compute_events = [e for e in events if _etype_str(e.type) == "COMPUTE_REQUESTED"] if events else []
    compute_events = sorted(compute_events, key=lambda e: (e.ts, e.event_id))[:limit] if compute_events else []
    items: List[ComputeRequestViewItem] = []
    for e in compute_events:
        payload = _payload_dict(e.payload)
        kind = payload.get("kind") or payload.get("compute_type") or payload.get("type") or "UNKNOWN"
        params = payload.get("params") or payload.get("parameters") or {}
        kwargs = dict(
            event_id=e.event_id,
            ts=e.ts,
            kind=kind,
            params_hash=e.payload_hash,
            params=params if include_params else None
        )
        items.append(ComputeRequestViewItem(**kwargs))
    return ComputeRequestsListResponse(session_id=session_id, items=items)
