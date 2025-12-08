from __future__ import annotations

from fastapi import APIRouter

from api.schemas.strategy import (
    StrategySuggestRequest,
    StrategySuggestResponse,
)
from core.services.strategy_planner_service import suggest_strategies_service


router = APIRouter(
    prefix="/v1/strategy",
    tags=["strategy-planner"],
)


@router.post("/suggest", response_model=StrategySuggestResponse)
def suggest_strategies(req: StrategySuggestRequest) -> StrategySuggestResponse:
    """
    Strategy Planner כ־API:
    ה־router נשאר דק:
    - מקבל StrategySuggestRequest מה־UI / לקוח חיצוני
    - מעביר לשכבת השירות (strategy_planner_service)
    - מחזיר StrategySuggestResponse עם רשימת אסטרטגיות מומלצות
    """
    strategies = suggest_strategies_service(req)
    return StrategySuggestResponse(strategies=strategies)
