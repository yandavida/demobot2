from __future__ import annotations
from typing import Protocol, List, Dict
from core.v2.models import V2Event
from collections import defaultdict

class EventStore(Protocol):
    def append(self, event: V2Event) -> None:
        ...
    def list(self, session_id: str) -> List[V2Event]:
        ...

class InMemoryEventStore:
    """
    In-memory append-only event store. No deduplication at store level.
    Events are stored per session, ordered deterministically by (ts, event_id).
    """
    def __init__(self) -> None:
        self._events: Dict[str, List[V2Event]] = defaultdict(list)

    def append(self, event: V2Event) -> None:
        self._events[event.session_id].append(event)

    def list(self, session_id: str) -> List[V2Event]:
        events = self._events.get(session_id, [])
        # Deterministic ordering: (ts, event_id)
        return sorted(events, key=lambda e: (e.ts, e.event_id))
