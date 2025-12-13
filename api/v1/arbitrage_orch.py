from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from core.arbitrage.models import ArbitrageConfig
from core.portfolio.models import Currency
from core.services.arbitrage_orchestration import (
    create_arbitrage_session,
    get_session_history,
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
