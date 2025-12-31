
from typing import Any, Dict, List
import time
import logging
from fastapi import HTTPException
from api.v2.read_models_schemas import (
    EventViewItem,
    EventsListResponse,
    SnapshotMetadataResponse,
    ComputeRequestViewItem,
    ComputeRequestsListResponse,
)
from api.v2.service import get_v2_service

logger = logging.getLogger(__name__)


def _etype_str(t: Any) -> str:
    return t.value if hasattr(t, "value") else str(t)


def _payload_dict(p: Any) -> Dict[str, Any]:
    return p if isinstance(p, dict) else {}


def list_events(session_id: str, *, limit: int, include_payload: bool) -> EventsListResponse:
    if not (1 <= limit <= 500):
        raise HTTPException(status_code=400, detail="limit must be between 1 and 500")
    svc = get_v2_service()
    if svc.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    start = time.perf_counter()
    from core.v2.event_ordering import stable_sort_events, event_id, unwrap_event
    events = svc.event_store.list(session_id) if hasattr(svc, "event_store") else []
    sorted_events = stable_sort_events(events)
    seen = set()
    items: List[EventViewItem] = []
    applied_version = 0
    for e in sorted_events:
        ev = unwrap_event(e)
        if event_id(e) in seen:
            continue
        seen.add(event_id(e))
        applied_version += 1
        kwargs = dict(
            event_id=event_id(e),
            ts=ev.ts,
            type=_etype_str(ev.type),
            payload_hash=ev.payload_hash,
            state_version=applied_version,
            payload=_payload_dict(ev.payload) if include_payload else None
        )
        items.append(EventViewItem(**kwargs))
        if len(items) >= limit:
            break
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.debug(
        "v2_read_model name=list_events session_id=%s limit=%s returned=%d elapsed_ms=%.2f",
        session_id, limit, len(items), elapsed_ms
    )
    return EventsListResponse(session_id=session_id, items=items)


def get_snapshot_metadata(session_id: str) -> SnapshotMetadataResponse:
    start = time.perf_counter()
    svc = get_v2_service()
    snap = svc.snapshot_store.latest(session_id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.debug(
        "v2_read_model name=get_snapshot_metadata session_id=%s limit=None returned=1 elapsed_ms=%.2f",
        session_id, elapsed_ms
    )
    return SnapshotMetadataResponse(
        session_id=snap.session_id,
        state_version=snap.version,
        state_hash=snap.state_hash,
        created_at=getattr(snap, "created_at", None) or getattr(snap, "ts", None),
    )


def list_compute_requests(session_id: str, *, limit: int, include_params: bool) -> ComputeRequestsListResponse:
    start = time.perf_counter()
    if not (1 <= limit <= 500):
        raise HTTPException(status_code=400, detail="limit must be between 1 and 500")

    svc = get_v2_service()
    if svc.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")

    from core.v2.event_ordering import stable_sort_events, event_id, unwrap_event

    events = svc.event_store.list(session_id) if hasattr(svc, "event_store") else []
    sorted_events = stable_sort_events(events)

    seen = set()
    items: List[ComputeRequestViewItem] = []

    for e in sorted_events:
        ev = unwrap_event(e)
        eid = event_id(e)

        if eid in seen:
            continue
        seen.add(eid)

        if _etype_str(ev.type) != "COMPUTE_REQUESTED":
            continue

        payload = _payload_dict(ev.payload)
        kind = payload.get("kind") or payload.get("compute_type") or payload.get("type") or "UNKNOWN"
        params = payload.get("params") or payload.get("parameters") or {}

        kwargs = dict(
            event_id=eid,
            ts=ev.ts,
            kind=kind,
            params_hash=ev.payload_hash,
            params=params if include_params else None,
        )
        items.append(ComputeRequestViewItem(**kwargs))

        if len(items) >= limit:
            break

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.debug(
        "v2_read_model name=list_compute_requests session_id=%s limit=%s returned=%d elapsed_ms=%.2f",
        session_id, limit, len(items), elapsed_ms
    )
    return ComputeRequestsListResponse(session_id=session_id, items=items)
