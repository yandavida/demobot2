from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field



# Event types
EventType = Literal[
    "QUOTE_INGESTED",
    "COMPUTE_REQUESTED",
    "PORTFOLIO_CREATED",
    "PORTFOLIO_POSITION_UPSERTED",
    "PORTFOLIO_POSITION_REMOVED"
]

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

# Portfolio event commands
class PortfolioCreatedCommand(BaseModel):
    type: Literal["PORTFOLIO_CREATED"] = Field(default="PORTFOLIO_CREATED")
    payload: Dict[str, Any]
    event_id: Optional[str] = None
    ts: Optional[datetime] = None

class PortfolioPositionUpsertedCommand(BaseModel):
    type: Literal["PORTFOLIO_POSITION_UPSERTED"] = Field(default="PORTFOLIO_POSITION_UPSERTED")
    payload: Dict[str, Any]
    event_id: Optional[str] = None
    ts: Optional[datetime] = None

class PortfolioPositionRemovedCommand(BaseModel):
    type: Literal["PORTFOLIO_POSITION_REMOVED"] = Field(default="PORTFOLIO_POSITION_REMOVED")
    payload: Dict[str, Any]
    event_id: Optional[str] = None
    ts: Optional[datetime] = None

from typing import Union
V2IngestCommand = Union[
    QuoteIngestCommand,
    ComputeRequestedCommand,
    PortfolioCreatedCommand,
    PortfolioPositionUpsertedCommand,
    PortfolioPositionRemovedCommand,
]
