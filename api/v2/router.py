from fastapi import APIRouter, Request, Response, status, HTTPException, Depends

from api.v2.schemas import CreateSessionResponse, IngestEventRequest, IngestEventResponse, SnapshotResponse
from api.v2.service import v2_service
from api.v2.correlation import get_or_create_correlation_id, attach_correlation_id
from api.v2.logging import log_request
from time import perf_counter

router = APIRouter(prefix="/api/v2")

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

@router.post("/sessions/{session_id}/events", response_model=IngestEventResponse)
async def ingest_event(session_id: str, req: IngestEventRequest, request: Request, response: Response, cid: str = Depends(correlation_id_dep)):
    t0 = perf_counter()
    try:
        state_version, applied = v2_service.ingest_event(session_id, req)
    except KeyError:
        elapsed = (perf_counter() - t0) * 1000
        log_request("POST", f"/api/v2/sessions/{session_id}/events", session_id, cid, 404, elapsed)
        raise HTTPException(status_code=404, detail="Session not found")
    elapsed = (perf_counter() - t0) * 1000
    log_request("POST", f"/api/v2/sessions/{session_id}/events", session_id, cid, 200, elapsed)
    return IngestEventResponse(session_id=session_id, state_version=state_version, applied=applied, correlation_id=cid)

@router.get("/sessions/{session_id}/snapshot", response_model=SnapshotResponse)
async def get_snapshot(session_id: str, request: Request, response: Response, cid: str = Depends(correlation_id_dep)):
    t0 = perf_counter()
    try:
        snap = v2_service.get_snapshot(session_id)
    except KeyError:
        elapsed = (perf_counter() - t0) * 1000
        log_request("GET", f"/api/v2/sessions/{session_id}/snapshot", session_id, cid, 404, elapsed)
        raise HTTPException(status_code=404, detail="Session not found")
    elapsed = (perf_counter() - t0) * 1000
    log_request("GET", f"/api/v2/sessions/{session_id}/snapshot", session_id, cid, 200, elapsed)
    return SnapshotResponse(
        session_id=snap.session_id,
        version=snap.version,
        state_hash=snap.state_hash,
        data=snap.data,
        correlation_id=cid,
    )

