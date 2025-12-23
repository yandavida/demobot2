from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


# Event types
EventType = Literal["QUOTE_INGESTED", "COMPUTE_REQUESTED"]

# Compute kind
ComputeKind = Literal["SNAPSHOT", "PORTFOLIO_RISK", "SCENARIO_GRID"]

class QuoteIngestCommand(BaseModel):
    type: EventType = Field(default="QUOTE_INGESTED")
    payload: Dict[str, Any]
    event_id: Optional[str] = None
    ts: Optional[datetime] = None


# New: ComputeRequestedCommand
class ComputeRequestedCommand(BaseModel):
    type: Literal["COMPUTE_REQUESTED"] = Field(default="COMPUTE_REQUESTED")
    payload: Dict[str, Any]
    request_id: Optional[str] = None
    event_id: Optional[str] = None
    ts: Optional[datetime] = None


# Union for API boundary
from typing import Union
V2IngestCommand = Union[QuoteIngestCommand, ComputeRequestedCommand]
