from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from core.arbitrage.models import ArbitrageConfig
from core.portfolio.models import Currency
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


class HistoryRequest(BaseModel):
    session_id: UUID
    symbol: Optional[str] = None


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


class OpportunityDetailOut(BaseModel):
    opportunity: dict[str, object]
    state: str | None
    signals: dict[str, float]
    reasons: list[dict[str, str]]


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


@router.post("/scan", response_model=List[OpportunityOut])
def scan(req: ScanRequest) -> List[OpportunityOut]:
    opportunities = ingest_quotes_and_scan(
        session_id=req.session_id,
        quotes_payload=[q.model_dump() for q in req.quotes],
        fx_rate_usd_ils=req.fx_rate_usd_ils,
    )
    return [OpportunityOut(**opp) for opp in opportunities]


@router.post("/history", response_model=List[OpportunityOut])
def history(req: HistoryRequest) -> List[OpportunityOut]:
    hist = get_session_history(
        session_id=req.session_id,
        symbol=req.symbol,
    )
    return [OpportunityOut(**opp) for opp in hist]


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


@router.get("/history-window", response_model=List[OpportunityOut])
def history_window(session_id: UUID, limit: int = 200, symbol: Optional[str] = None) -> List[OpportunityOut]:
    hist = get_history_window(session_id=session_id, symbol=symbol, limit=limit)
    return [OpportunityOut(**opp) for opp in hist]
