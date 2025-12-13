from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ArbitrageEventType(str, Enum):
    SNAPSHOT_INGESTED = "SNAPSHOT_INGESTED"
    OPPORTUNITY_UPSERTED = "OPPORTUNITY_UPSERTED"
    OPPORTUNITY_EXPIRED = "OPPORTUNITY_EXPIRED"


@dataclass
class ArbitrageEvent:
    as_of: datetime
    event_type: ArbitrageEventType
    payload: dict[str, object] | None = None


__all__ = ["ArbitrageEvent", "ArbitrageEventType"]
