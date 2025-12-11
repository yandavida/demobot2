from __future__ import annotations

from fastapi import APIRouter

from core.services.portfolio_valuation import (
    PublicValuationRequest,
    PublicValuationResponse,
    valuate_portfolio,
)


router = APIRouter(
    prefix="/v1/portfolio",
    tags=["portfolio"],
)


@router.post("/valuate", response_model=PublicValuationResponse)
def valuate(req: PublicValuationRequest) -> PublicValuationResponse:
    """Public portfolio valuation endpoint."""

    return valuate_portfolio(req)

