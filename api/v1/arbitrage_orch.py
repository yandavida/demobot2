from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ValidationError, model_validator

try:
    from pydantic_core import ValidationError as CoreValidationError
except Exception:  # pragma: no cover
    CoreValidationError = ValidationError


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
logger = logging.getLogger(__name__)


# -------------------------
# Request / Input models
# -------------------------


class QuoteIn(BaseModel):
    symbol: str
    venue: str
    ccy: str = "USD"
    bid: float | None = None
    ask: float | None = None
    size: float | None = None
    fees_bps: float | None = 0.0
    latency_ms: float | None = None


class CreateSessionRequest(BaseModel):
    base_currency: Currency = "ILS"
    min_edge_bps: float = 5.0
    max_quantity: float = 1.0


class CreateSessionResponse(BaseModel):
    session_id: UUID


class ScanRequest(BaseModel):
    session_id: UUID
    quotes: List[QuoteIn]
    fx_rate_usd_ils: float = 3.5
    strict_validation: bool = False


class HistoryRequest(BaseModel):
    session_id: UUID
    symbol: Optional[str] = None


# -------------------------
# Validation models
# -------------------------


class QuoteValidationOut(BaseModel):
    """
    Output contract for quote validation.

    Supports "new" contract payloads like:
      { total, valid, invalid, errors: [ {index, messages, ...} ], warnings: [...] }

    And remains permissive enough to accept legacy-ish shapes.
    """

    # New contract fields
    total: int | None = None
    valid: int | None = None
    invalid: int | None = None
    errors: list[object] = Field(default_factory=list)
    warnings: list[object] = Field(default_factory=list)

    # Convenience / compatibility
    as_of: str | None = None
    error_count: int = 0
    warning_count: int = 0

    @model_validator(mode="after")
    def _compute_counts(self) -> "QuoteValidationOut":
        self.error_count = len(self.errors or [])
        self.warning_count = len(self.warnings or [])
        return self


# Backward compatibility alias
ValidationSummaryOut = QuoteValidationOut


# -------------------------
# Output / Response models
# -------------------------


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

    # Optional: attach same summary per opportunity if needed by UI
    quote_validation: QuoteValidationOut | None = None


class ScanResponse(BaseModel):
    opportunities: List[OpportunityOut]

    # Preferred field name going forward
    quote_validation: QuoteValidationOut | None = None

    # Backward-compat field name expected by tests
    validation_summary: ValidationSummaryOut | None = None


# Alias expected by some imports/tests
OpportunitiesWithValidationResponse = ScanResponse


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


# -------------------------
# Router hygiene
# -------------------------


def check_route_collisions(target_router: APIRouter) -> None:
    """Ensure there are no duplicate method/path combinations on the router."""
    seen: set[tuple[str, str]] = set()
    collisions: list[tuple[str, str]] = []

    for route in target_router.routes:
        methods = getattr(route, "methods", None) or []
        path = getattr(route, "path", None)
        if not path:
            continue
        for method in methods:
            key = (str(method).upper(), str(path))
            if key in seen:
                collisions.append(key)
            else:
                seen.add(key)

    if collisions:
        for method, path in collisions:
            logger.error("Duplicate route detected: %s %s", method, path)
        formatted = ", ".join(f"{method} {path}" for method, path in collisions)
        raise ValueError(f"Duplicate routes detected: {formatted}")


# -------------------------
# Routes
# -------------------------


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
        scan_result = ingest_quotes_and_scan(
            session_id=req.session_id,
            quotes_payload=[q.model_dump() for q in req.quotes],
            fx_rate_usd_ils=req.fx_rate_usd_ils,
            strict_validation=req.strict_validation,
        )
    except Exception as exc:
        # Strict mode: any validation failure must surface as HTTP 400
        if req.strict_validation:
            errors = exc.errors() if hasattr(exc, "errors") else [{"message": str(exc)}]
            raise HTTPException(
                status_code=400,
                detail={"errors": errors, "error_count": len(errors)},
            ) from exc
        raise

    validation_raw = (
        scan_result.get("validation_summary")
        or scan_result.get("quote_validation")
        or scan_result.get("quote_validation_summary")
    )
    validation = QuoteValidationOut(**validation_raw) if isinstance(validation_raw, dict) else None

    opportunities: list[OpportunityOut] = []
    for opp in scan_result.get("opportunities", []):
        payload = dict(opp)
        if validation is not None:
            payload["quote_validation"] = validation
        opportunities.append(OpportunityOut(**payload))

    return ScanResponse(
        opportunities=opportunities,
        quote_validation=validation,
        validation_summary=validation,
    )


@router.post("/history", response_model=List[OpportunityOut])
def history(req: HistoryRequest) -> List[OpportunityOut]:
    hist = get_session_history(session_id=req.session_id, symbol=req.symbol)
    return [OpportunityOut(**opp) for opp in hist]


@router.get("/top", response_model=List[RecommendationOut])
def top(
    session_id: UUID,
    limit: int = 10,
    symbol: Optional[str] = None,
) -> List[RecommendationOut]:
    recs = get_top_recommendations(session_id=session_id, limit=limit, symbol=symbol)
    return [RecommendationOut(**rec) for rec in recs]


@router.get("/readiness", response_model=List[ReadinessOut])
def readiness(session_id: UUID, symbol: Optional[str] = None) -> List[ReadinessOut]:
    states = get_readiness_states(session_id=session_id, symbol=symbol)
    return [ReadinessOut(**state) for state in states]


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityDetailOut)
def opportunity_detail(session_id: UUID, opportunity_id: str) -> OpportunityDetailOut:
    detail = get_opportunity_detail(session_id=session_id, opportunity_id=opportunity_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return OpportunityDetailOut(**detail)


@router.get("/history-window", response_model=List[OpportunityOut])
def history_window(
    session_id: UUID,
    limit: int = 200,
    symbol: Optional[str] = None,
) -> List[OpportunityOut]:
    hist = get_history_window(session_id=session_id, symbol=symbol, limit=limit)
    return [OpportunityOut(**opp) for opp in hist]


check_route_collisions(router)
