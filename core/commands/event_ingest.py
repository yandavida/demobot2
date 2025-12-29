from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.commands.base import BaseCommand
from core.v2.models import EventType


@dataclass(frozen=True)
class IngestEventCommand(BaseCommand):
    event_id: str | None
    ts: datetime | None
    type: EventType
    payload: dict[str, Any]
