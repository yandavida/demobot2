from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field

from core.arbitrage.models import ArbitrageConfig
from core.portfolio.models import Currency
from core.quote_validation import QuoteValidationError
from core.services.arbitrage_orchestration import (
    create_arbitrage_session,
    get_history_window,
    get_opportunity_detail,
    get_readiness_states,
    get_session_history,
    get_top_recommendations,
    ingest_quotes_and_scan,
)

router = APIRouter(prefix="/v1/arbitrage", tags=["arbitrage"])

logger = logging.getLogger(__name__)


class QuoteIn(BaseModel):
    symbol: str
    venue: str
    ccy: str = "USD"
    bid: float | None = None
    ask: float | None = None
    size: float | None = None
    fees_bps: float | None = 0.0


class CreateSessionRequest(BaseModel):
    base_currency: Currency = "ILS"
    min_edge_bps: float = 5.0
    max_quantity: float = 1.0


class CreateSessionResponse(BaseModel):
    session_id: UUID


class ScanRequest(BaseModel):
    session_id: UUID
    fx_rate_usd_ils: float = 3.5
    quotes: List[QuoteIn]
    strict_validation: bool = False


class ValidationSummaryOut(BaseModel):
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0


class ScanResponse(BaseModel):
    opportunities: List[OpportunityOut]
    validation_summary: ValidationSummaryOut | None = None


class OpportunityOut(BaseModel):
    timestamp: str
    opportunity_id: str
    symbol: str
    buy_venue: str
    sell_venue: str
    quantity: float
    gross_edge_per_unit: float
    gross_edge_total: float
    currency: str
    edge_bps: float
    execution_readiness: dict[str, object] | None = None
    execution_decision: dict[str, object] | None = None


class HistoryRequest(BaseModel):
    session_id: UUID
    symbol: Optional[str] = None


class OpportunitiesWithValidationResponse(BaseModel):
    opportunities: List[OpportunityOut]
    validation_summary: ValidationSummaryOut | None = None


class ReadinessOut(BaseModel):
    opportunity_id: str
    symbol: str | None = None
    first_seen: str
    last_seen: str
    seen_count: int
    last_edge_bps: float
    last_net_edge_bps: float
    state: str


class RecommendationOut(BaseModel):
    opportunity_id: str
    rank: int
    quality_score: float
    reasons: list[dict[str, str]]
    signals: dict[str, float]
    economics: dict[str, object]
    execution_readiness: dict[str, object] | None = None
    execution_decision: dict[str, object] | None = None


class OpportunityDetailOut(BaseModel):
    opportunity: dict[str, object]
    state: str | None
    signals: dict[str, float]
    reasons: list[dict[str, str]]
    execution_readiness: dict[str, object] | None = None
    execution_decision: dict[str, object] | None = None


def check_route_collisions(target_router: APIRouter) -> None:
    """Ensure there are no duplicate method/path combinations on the router."""

    seen: set[tuple[str, str]] = set()
    collisions: list[tuple[str, str]] = []

    for route in target_router.routes:
        for method in route.methods or []:
            key = (method.upper(), route.path)
            if key in seen:
                collisions.append(key)
            else:
                seen.add(key)

    if collisions:
        for method, path in collisions:
            logger.error("Duplicate route detected: %s %s", method, path)
        formatted = ", ".join(f"{method} {path}" for method, path in collisions)
        raise ValueError(f"Duplicate routes detected: {formatted}")


@router.post("/sessions", response_model=CreateSessionResponse)
def create_session(req: CreateSessionRequest) -> CreateSessionResponse:
    config = ArbitrageConfig(
        min_edge_bps=req.min_edge_bps,
        allow_same_venue=False,
        default_size=req.max_quantity,
    )
    session_id = create_arbitrage_session(
        base_currency=req.base_currency,
        config=config,
    )
    return CreateSessionResponse(session_id=session_id)


@router.post("/scan", response_model=ScanResponse)
def scan(req: ScanRequest) -> ScanResponse:
    try:
        result = ingest_quotes_and_scan(
            session_id=req.session_id,
            quotes_payload=[q.model_dump() for q in req.quotes],
            fx_rate_usd_ils=req.fx_rate_usd_ils,
            strict_validation=req.strict_validation,
            include_validation_summary=True,
        )
    except QuoteValidationError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=exc.summary.to_dict()) from exc

    opportunities, validation_summary = result
    return ScanResponse(
        opportunities=[OpportunityOut(**opp) for opp in opportunities],
        validation_summary=validation_summary.to_dict() if validation_summary else None,
    )


@router.post("/history", response_model=OpportunitiesWithValidationResponse)
def history(req: HistoryRequest) -> OpportunitiesWithValidationResponse:
    hist, validation_summary = get_session_history(
        session_id=req.session_id,
        symbol=req.symbol,
        include_validation_summary=True,
    )
    return OpportunitiesWithValidationResponse(
        opportunities=[OpportunityOut(**opp) for opp in hist],
        validation_summary=validation_summary.to_dict() if validation_summary else None,
    )


@router.get("/top", response_model=List[RecommendationOut])
def top(session_id: UUID, limit: int = 10, symbol: Optional[str] = None) -> List[RecommendationOut]:
    recs = get_top_recommendations(session_id=session_id, limit=limit, symbol=symbol)
    return [RecommendationOut(**rec) for rec in recs]


@router.get("/readiness", response_model=List[ReadinessOut])
def readiness(session_id: UUID, symbol: Optional[str] = None) -> List[ReadinessOut]:
    readiness_states = get_readiness_states(session_id=session_id, symbol=symbol)
    return [ReadinessOut(**state) for state in readiness_states]


@router.get(
    "/opportunities/{opportunity_id}",
    response_model=OpportunityDetailOut,
)
def opportunity_detail(session_id: UUID, opportunity_id: str) -> OpportunityDetailOut:
    detail = get_opportunity_detail(session_id=session_id, opportunity_id=opportunity_id)
    if detail is None:
        return OpportunityDetailOut(opportunity={}, state=None, signals={}, reasons=[])
    return OpportunityDetailOut(**detail)


@router.get("/history-window", response_model=OpportunitiesWithValidationResponse)
def history_window(
    session_id: UUID, limit: int = 200, symbol: Optional[str] = None
) -> OpportunitiesWithValidationResponse:
    hist, validation_summary = get_history_window(
        session_id=session_id, symbol=symbol, limit=limit, include_validation_summary=True
    )
    return OpportunitiesWithValidationResponse(
        opportunities=[OpportunityOut(**opp) for opp in hist],
        validation_summary=validation_summary.to_dict() if validation_summary else None,
    )


check_route_collisions(router)
