
from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ReasonOut(BaseModel):
    code: str
    message: str
    observed: Optional[float] = None
    threshold: Optional[float] = None
    unit: Optional[str] = None
    context: Dict[str, str] = Field(default_factory=dict)


class MetricValueOut(BaseModel):
    name: str
    value: Optional[float] = None
    unit: Optional[str] = None
    direction: Literal["higher_is_better", "lower_is_better", "neutral"]


class OpportunityDecisionTraceOut(BaseModel):
    verdict: Literal["ACCEPTED", "REJECTED"]
    reasons: List[ReasonOut]
    metrics: List[MetricValueOut]


class OpportunityViewOut(BaseModel):
    opportunity_id: str
    symbol: str
    buy_venue: str
    sell_venue: str
    prices: Dict[str, float]  # {"buy_ask": ..., "sell_bid": ...}
    decision_trace: OpportunityDecisionTraceOut


class LatestOpportunitiesOut(BaseModel):
    items: List[OpportunityViewOut]
