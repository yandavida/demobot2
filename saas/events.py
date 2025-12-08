# saas/events.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List


class EventName(str, Enum):
    POSITION_CREATED = "position_created"
    POSITION_CLOSED = "position_closed"
    RISK_RECALCULATED = "risk_recalculated"
    CUSTOMER_LIMIT_HIT = "customer_limit_hit"


@dataclass
class Event:
    name: EventName
    payload: Dict[str, Any]


EventHandler = Callable[[Event], None]


class EventBus:
    def __init__(self):
        self._handlers: Dict[EventName, List[EventHandler]] = {}

    def subscribe(self, name: EventName, handler: EventHandler) -> None:
        self._handlers.setdefault(name, []).append(handler)

    def publish(self, event: Event) -> None:
        for handler in self._handlers.get(event.name, []):
            handler(event)


# אינסטנס גלובלי בסיסי – אפשר להחליף בעתיד במשהו רציני יותר
event_bus = EventBus()
