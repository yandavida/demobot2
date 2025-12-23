from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field

EventType = Literal["QUOTE_INGESTED"]

class QuoteIngestCommand(BaseModel):
    type: EventType = Field(default="QUOTE_INGESTED")
    payload: Dict[str, Any]
    event_id: Optional[str] = None
    ts: Optional[datetime] = None
