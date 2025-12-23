import logging
logger = logging.getLogger("demobot.v2")
from fastapi import APIRouter, Request, Response, status, HTTPException, Depends

from api.v2.schemas import CreateSessionResponse, IngestEventResponse, SnapshotResponse
from api.v2.commands import QuoteIngestCommand
from api.v2.validators import validate_quote_payload
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

@router.post("/sessions/{session_id}/events", response_model=IngestEventResponse, status_code=201)
async def ingest_event(session_id: str, req: QuoteIngestCommand, request: Request):
    cid = getattr(request.state, "correlation_id", None)
    # Strict command boundary: only QUOTE_INGESTED supported here
    if req.type != "QUOTE_INGESTED":
        raise HTTPException(status_code=400, detail={"detail": "Only QUOTE_INGESTED supported in V2 command boundary"})
    validate_quote_payload(req.payload)
    try:
        state_version, applied = v2_service.ingest_event(
            session_id,
            event_id=req.event_id,
            ts=req.ts,
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

