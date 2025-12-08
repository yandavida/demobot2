from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas.fx import FxForwardRequest, FxForwardResponse
from core.services.fx_service import analyze_fx_forward_service
import logging

logger = logging.getLogger("demobot.fx")


router = APIRouter(
    prefix="/v1/fx",
    tags=["fx"],
)


@router.post("/forward/analyze", response_model=FxForwardResponse)
def analyze_fx_forward(req: FxForwardRequest) -> FxForwardResponse:
    """
    Endpoint דק – מעביר את הבקשה ל-service לוגי ומחזיר תשובה.
    """
    logger.info(
        "FX forward analyze request",
        extra={
            "base_ccy": req.base_ccy,
            "quote_ccy": req.quote_ccy,
            "notional": req.notional,
            "direction": req.direction,
        },
    )

    if req.maturity_date <= req.valuation_date:
        logger.warning(
            "FX validation error: maturity <= valuation",
            extra={
                "valuation_date": req.valuation_date.isoformat(),
                "maturity_date": req.maturity_date.isoformat(),
            },
        )
        raise HTTPException(
            status_code=422,
            detail="maturity_date must be after valuation_date",
        )

    try:
        data = analyze_fx_forward_service(req)
    except ValueError as e:
        logger.warning(
            "FX service validation error",
            extra={"error": str(e)},
        )
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("FX engine internal failure")
        raise HTTPException(status_code=500, detail=f"FX engine failure: {e}")

    logger.info("FX forward analyze success")
    return FxForwardResponse(**data)
