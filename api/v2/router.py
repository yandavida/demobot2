import logging
logger = logging.getLogger("demobot.v2")
from fastapi import APIRouter, Request, Response, status, HTTPException, Depends
from api.v2.read_models import list_events, get_snapshot_metadata, list_compute_requests
from api.v2.read_models_opportunities_schemas import LatestOpportunitiesOut
from api.v2.read_models_schemas import EventsListResponse, SnapshotMetadataResponse, ComputeRequestsListResponse
from api.v2.schemas import CreateSessionResponse, IngestEventResponse, SnapshotResponse
from api.v2.commands import V2IngestCommand
from api.v2.validators import validate_quote_payload, validate_compute_payload
from api.v2.service import v2_service
from api.v2.correlation import get_or_create_correlation_id, attach_correlation_id
from api.v2.logging import log_request
from time import perf_counter


router = APIRouter()

# תלות ל-correlation id (חייב להיות לפני כל שימוש)
async def correlation_id_dep(request: Request, response: Response):
    cid = get_or_create_correlation_id(request)
    attach_correlation_id(response, cid)
    return cid

# יצירת snapshot מפורש (לצורך בדיקות ו-API)
@router.post("/sessions/{session_id}/snapshot", response_model=SnapshotResponse)
async def create_snapshot(session_id: str, request: Request, response: Response, cid: str = Depends(correlation_id_dep)):
    t0 = perf_counter()
    try:
        snap = v2_service.create_snapshot(session_id)
    except HTTPException:
        elapsed = (perf_counter() - t0) * 1000
        log_request("POST", f"/api/v2/sessions/{session_id}/snapshot", session_id, cid, 404, elapsed)
        raise
    except Exception:
        elapsed = (perf_counter() - t0) * 1000
        log_request("POST", f"/api/v2/sessions/{session_id}/snapshot", session_id, cid, 500, elapsed)
        raise HTTPException(status_code=500, detail="Internal Server Error")
    elapsed = (perf_counter() - t0) * 1000
    log_request("POST", f"/api/v2/sessions/{session_id}/snapshot", session_id, cid, 201, elapsed)
    response.status_code = status.HTTP_201_CREATED
    return SnapshotResponse(
        session_id=snap.session_id,
        version=snap.version,
        state_hash=snap.state_hash,
        data=snap.data,
        correlation_id=cid,
    )

# --- עזר: בדיקת קיום session ---
def assert_session_exists(session_id: str) -> None:
    if v2_service.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")

# --- GET /sessions/{session_id}/snapshot ---
@router.get("/sessions/{session_id}/snapshot", response_model=SnapshotResponse)
async def get_snapshot(session_id: str, request: Request, response: Response, cid: str = Depends(correlation_id_dep)):
    t0 = perf_counter()
    assert_session_exists(session_id)
    try:
        snap = v2_service.get_snapshot(session_id)
    except HTTPException:
        elapsed = (perf_counter() - t0) * 1000
        log_request("GET", f"/api/v2/sessions/{session_id}/snapshot", session_id, cid, 404, elapsed)
        raise
    except Exception:
        elapsed = (perf_counter() - t0) * 1000
        log_request("GET", f"/api/v2/sessions/{session_id}/snapshot", session_id, cid, 500, elapsed)
        raise HTTPException(status_code=500, detail="Internal Server Error")
    elapsed = (perf_counter() - t0) * 1000
    log_request("GET", f"/api/v2/sessions/{session_id}/snapshot", session_id, cid, 200, elapsed)
    return SnapshotResponse(
        session_id=snap.session_id,
        version=snap.version,
        state_hash=snap.state_hash,
        data=snap.data,
        correlation_id=cid,
    )

# --- GET /sessions/{session_id}/events ---
@router.get("/sessions/{session_id}/events", response_model=EventsListResponse)
async def get_events_list(session_id: str, limit: int = 200, include_payload: bool = False):
    assert_session_exists(session_id)
    return list_events(session_id, limit=limit, include_payload=include_payload)

# --- GET /sessions/{session_id}/compute/requests ---
@router.get("/sessions/{session_id}/compute/requests", response_model=ComputeRequestsListResponse)
async def get_compute_requests(session_id: str, limit: int = 200, include_params: bool = False):
    assert_session_exists(session_id)
    return list_compute_requests(session_id, limit=limit, include_params=include_params)

# --- GET /sessions/{session_id}/snapshot/metadata ---
@router.get("/sessions/{session_id}/snapshot/metadata", response_model=SnapshotMetadataResponse)
async def get_snapshot_metadata_view(session_id: str):
    assert_session_exists(session_id)
    return get_snapshot_metadata(session_id)

@router.get("/opportunities/latest", response_model=LatestOpportunitiesOut, status_code=200)
async def get_latest_opportunities(session_id: str, limit: int = 50):
    try:
        return v2_service.get_latest_opportunity_views(session_id=session_id, limit=limit)
    except Exception:
        return LatestOpportunitiesOut(items=[])

async def correlation_id_dep(request: Request, response: Response):
    cid = get_or_create_correlation_id(request)
    attach_correlation_id(response, cid)
    return cid

@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(request: Request, response: Response, cid: str = Depends(correlation_id_dep)):
    t0 = perf_counter()
    session_id = v2_service.create_session()
    elapsed = (perf_counter() - t0) * 1000
    log_request("POST", "/api/v2/sessions", session_id, cid, status.HTTP_201_CREATED, elapsed)
    response.status_code = status.HTTP_201_CREATED
    return CreateSessionResponse(session_id=session_id)

@router.post("/sessions/{session_id}/events", response_model=IngestEventResponse, status_code=201)
async def ingest_event(session_id: str, req: V2IngestCommand, request: Request):
    cid = getattr(request.state, "correlation_id", None)
    # דטרמיניזם מלא: dispatch לפי type
    if req.type == "QUOTE_INGESTED":
        validate_quote_payload(req.payload)
    elif req.type == "COMPUTE_REQUESTED":
        validate_compute_payload(req.payload)
    else:
        raise HTTPException(status_code=400, detail={"detail": f"unsupported command type: {req.type}"})
    try:
        state_version, applied = v2_service.ingest_event(
            session_id=session_id,
            event_id=getattr(req, "event_id", None),
            ts=getattr(req, "ts", None),
            type=req.type,
            payload=req.payload,
        )
        return IngestEventResponse(
            session_id=session_id,
            state_version=state_version,
            applied=applied,
            correlation_id=cid,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "v2.ingest_event failed",
            extra={
                "correlation_id": cid,
                "session_id": session_id,
                "event_id": getattr(req, "event_id", None),
                "event_type": getattr(req, "type", None),
            },
        )
        raise HTTPException(status_code=500, detail={"detail": "Internal Server Error"}) from exc

