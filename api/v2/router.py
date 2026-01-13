
from fastapi import APIRouter, Request, Response, status, HTTPException, Depends
from api.v2.service import get_v2_service
from api.v2.read_models import list_events, get_snapshot_metadata, list_compute_requests
from api.v2.read_models_opportunities_schemas import LatestOpportunitiesOut
from api.v2.read_models_schemas import EventsListResponse, SnapshotMetadataResponse, ComputeRequestsListResponse
from api.v2.schemas import CreateSessionResponse, IngestEventResponse, SnapshotResponse
from api.v2.commands import V2IngestCommand
from api.v2.validators import validate_quote_payload, validate_compute_payload
from api.v2.force_raise_hook import should_force_raise_for_tests
from api.v2.correlation import get_or_create_correlation_id, attach_correlation_id
from api.v2.logging import log_request
from api.v2.portfolio_read_model import get_portfolio_summary
from api.v2.portfolio_schemas import PortfolioSummaryOut

router = APIRouter()




# --- Correlation ID Dependency ---
async def correlation_id_dep(request: Request, response: Response):
    cid = get_or_create_correlation_id(request)
    attach_correlation_id(response, cid)
    return cid


# --- Helper: Assert Session Exists ---
def assert_session_exists(session_id: str) -> None:
    svc = get_v2_service()
    if svc.get_session(session_id) is None:
        # Use canonical envelope for not-found errors.
        from api.v2.http_errors import not_found

        not_found("session_not_found", "Session not found")

# --- Endpoints ---

@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(request: Request, response: Response, cid: str = Depends(correlation_id_dep)):
    if should_force_raise_for_tests():
        raise RuntimeError("forced error for tests")
    svc = get_v2_service()
    session_id = svc.create_session()
    log_request("POST", "/api/v2/sessions", session_id, cid, status.HTTP_201_CREATED, 0)
    response.status_code = status.HTTP_201_CREATED
    return CreateSessionResponse(session_id=session_id)

@router.post("/sessions/{session_id}/events", response_model=IngestEventResponse, status_code=201)
async def ingest_event(session_id: str, req: V2IngestCommand, request: Request):
    cid = getattr(request.state, "correlation_id", None)
    svc = get_v2_service()
    if req.type == "QUOTE_INGESTED":
        validate_quote_payload(req.payload)
    elif req.type == "COMPUTE_REQUESTED":
        validate_compute_payload(req.payload)
    elif req.type in {"PORTFOLIO_CREATED", "PORTFOLIO_POSITION_UPSERTED", "PORTFOLIO_POSITION_REMOVED"}:
        if not isinstance(req.payload, dict):
            from api.v2.http_errors import bad_request

            bad_request("invalid_portfolio_payload", "payload must be a dict for portfolio events")
        if req.type == "PORTFOLIO_CREATED":
            portfolio = req.payload.get("portfolio")
            if portfolio is not None and not isinstance(portfolio, dict):
                from api.v2.http_errors import bad_request

                bad_request("invalid_portfolio_payload", "portfolio must be a dict if present")
        elif req.type == "PORTFOLIO_POSITION_UPSERTED":
            position = req.payload.get("position")
            if not isinstance(position, dict):
                from api.v2.http_errors import bad_request

                bad_request("invalid_portfolio_payload", "position must be a dict")
        elif req.type == "PORTFOLIO_POSITION_REMOVED":
            position_id = req.payload.get("position_id")
            if not (isinstance(position_id, str) or (hasattr(position_id, "__str__") and not isinstance(position_id, dict))):
                from api.v2.http_errors import bad_request

                bad_request("invalid_portfolio_payload", "position_id must be a string-like value")
    else:
        from api.v2.http_errors import bad_request

        bad_request("unsupported_command_type", f"unsupported command type: {req.type}")
    try:
        state_version, applied = svc.ingest_event(
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
    except ValueError as ve:
        # Map service-raised ErrorEnvelope carried in ValueError -> HTTP 400
        from core.validation.error_envelope import ErrorEnvelope
        from api.v2.http_errors import raise_http

        detail = ve.args[0] if ve.args else None
        if isinstance(detail, ErrorEnvelope) or (isinstance(detail, dict) and detail.get("category") is not None):
            raise_http(detail, 400)
        raise
    except Exception:
        from core.v2.errors import EventConflictError

        if isinstance(Exception, EventConflictError):
            # defensive noop; keep logic explicit below
            pass

        # Re-raise locally to route EventConflictError to a 409 mapping
        try:
            raise
        except EventConflictError as exc:
            from api.v2.http_errors import raise_http
            from core.validation.error_envelope import ErrorEnvelope

            env = ErrorEnvelope(
                category="CONFLICT",
                code="event_conflict",
                message="Event conflict",
                details={
                    "reason": "conflicting event payload for existing event_id",
                    "event_id": getattr(exc, "event_id", None),
                },
            )
            raise_http(env, status.HTTP_409_CONFLICT)
        except Exception:
            # Map core MarketSnapshotNotFoundError -> 404
            from core.market_data.errors import MarketSnapshotNotFoundError

            try:
                raise
            except MarketSnapshotNotFoundError as mne:
                from api.v2.http_errors import raise_http
                from core.validation.error_envelope import ErrorEnvelope

                env = ErrorEnvelope(
                    category="VALIDATION",
                    code="market_snapshot_not_found",
                    message="Market snapshot not found",
                    details={"snapshot_id": getattr(mne, "snapshot_id", None)},
                )
                raise_http(env, status.HTTP_404_NOT_FOUND)
        except HTTPException:
            raise
        except Exception:
            from api.v2.service import should_force_raise_for_tests
            if should_force_raise_for_tests():
                raise
            from api.v2.http_errors import internal_error

            internal_error()

@router.post("/sessions/{session_id}/snapshot", response_model=SnapshotResponse)
async def create_snapshot(session_id: str, request: Request, response: Response, cid: str = Depends(correlation_id_dep)):
    svc = get_v2_service()
    try:
        snap = svc.create_snapshot(session_id)
    except HTTPException:
        raise
    except Exception:
        from api.v2.service import should_force_raise_for_tests
        if should_force_raise_for_tests():
            raise
        from api.v2.http_errors import internal_error

        internal_error()
    response.status_code = status.HTTP_201_CREATED
    return SnapshotResponse(
        session_id=snap.session_id,
        version=snap.version,
        state_hash=snap.state_hash,
        data=snap.data,
        correlation_id=cid,
    )

@router.get("/sessions/{session_id}/snapshot", response_model=SnapshotResponse)
async def get_snapshot(session_id: str, request: Request, response: Response, cid: str = Depends(correlation_id_dep)):
    assert_session_exists(session_id)
    svc = get_v2_service()
    snap = svc.get_snapshot(session_id)
    return SnapshotResponse(
        session_id=snap.session_id,
        version=snap.version,
        state_hash=snap.state_hash,
        data=snap.data,
        correlation_id=cid,
    )

@router.get("/sessions/{session_id}/events", response_model=EventsListResponse)
async def get_events_list(session_id: str, limit: int = 200, include_payload: bool = False):
    assert_session_exists(session_id)
    return list_events(session_id, limit=limit, include_payload=include_payload)

@router.get("/sessions/{session_id}/compute/requests", response_model=ComputeRequestsListResponse)
async def get_compute_requests(session_id: str, limit: int = 200, include_params: bool = False):
    assert_session_exists(session_id)
    return list_compute_requests(session_id, limit=limit, include_params=include_params)

@router.get("/sessions/{session_id}/snapshot/metadata", response_model=SnapshotMetadataResponse)
async def get_snapshot_metadata_view(session_id: str):
    assert_session_exists(session_id)
    return get_snapshot_metadata(session_id)

@router.get("/opportunities/latest", response_model=LatestOpportunitiesOut, status_code=200)
async def get_latest_opportunities(session_id: str, limit: int = 50):
    try:
        svc = get_v2_service()
        return svc.get_latest_opportunity_views(session_id=session_id, limit=limit)
    except Exception:
        from api.v2.service import should_force_raise_for_tests
        if should_force_raise_for_tests():
            raise
        return LatestOpportunitiesOut(items=[])

@router.get("/sessions/{session_id}/portfolio/summary", response_model=PortfolioSummaryOut)
async def get_portfolio_summary_view(session_id: str, request: Request, response: Response, cid: str = Depends(correlation_id_dep)):
    assert_session_exists(session_id)
    summary = get_portfolio_summary(session_id)
    # correlation_id נשמר רק בכותרת, לא ב-json
    return summary

