
from __future__ import annotations

from typing import Any, List, Sequence, TypeVar

T = TypeVar("T")

def unwrap_event(e: Any) -> Any:
    """
    Normalize event container -> raw V2Event.
    Supports:
      - V2Event (has .event_id/.ts/.type/.payload_hash/.payload)
      - AppliedEvent-like wrappers (has .event attribute)
    """
    return getattr(e, "event", e)

def event_id(e: Any) -> str:
    """
    Stable accessor for event id across containers.
    """
    ev = unwrap_event(e)
    eid = getattr(ev, "event_id", None) or getattr(e, "event_id", None)
    if eid is None:
        raise AttributeError("Event object has no event_id")
    return str(eid)

def stable_sort_events(events: Sequence[T]) -> List[T]:
    """
    Deterministic ordering:
      primary: ts
      secondary: event_id (tie-breaker)
    Works across V2Event and AppliedEvent containers.
    """
    def _key(x: Any) -> tuple:
        ev = unwrap_event(x)
        return (ev.ts, event_id(x))

    return sorted(list(events), key=_key)
