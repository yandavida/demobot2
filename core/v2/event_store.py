from __future__ import annotations
from typing import Protocol, List, Dict
from core.v2.models import V2Event
from core.v2.event_ordering import stable_sort_events
from collections import defaultdict

class EventStore(Protocol):
    def list_after_version(self, session_id: str, after_version: int) -> List[V2Event]:
        ...
    def append(self, event: V2Event) -> None:
        ...
    def list(self, session_id: str) -> List[V2Event]:
        ...

class InMemoryEventStore:
    def list_after_version(self, session_id: str, after_version: int) -> List[V2Event]:
        """החזר את כל האירועים עם applied_version > after_version (לפי event_id ייחודי, דטרמיניסטי)."""
        events = self.list(session_id)
        events = stable_sort_events(events)
        seen = set()
        applied_version = 0
        tail = []
        for e in events:
            if e.event_id in seen:
                continue
            seen.add(e.event_id)
            applied_version += 1
            if applied_version > after_version:
                tail.append(e)
        return tail
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
