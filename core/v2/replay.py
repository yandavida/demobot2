from __future__ import annotations
from typing import Sequence, Dict, Any
from core.v2.models import V2Event, hash_snapshot, AppliedEvent, Snapshot
def replay_applied(applied: Sequence[AppliedEvent]) -> Dict[str, Any]:
    """
    Replay a sequence of AppliedEvent into a dict, ordered strictly by state_version.
    """
    applied_sorted = sorted(applied, key=lambda ae: ae.state_version)
    data = {}
    for ae in applied_sorted:
        if ae.event.event_id not in data:
            data[ae.event.event_id] = ae.event.payload
    return data

def replay_from_snapshot(snapshot: Snapshot, applied_tail: Sequence[AppliedEvent]) -> Dict[str, Any]:
    """
    Replay from a snapshot and a tail of AppliedEvents.
    """
    data = dict(snapshot.data)
    tail_sorted = sorted(applied_tail, key=lambda ae: ae.state_version)
    for ae in tail_sorted:
        if ae.event.event_id not in data:
            data[ae.event.event_id] = ae.event.payload
    return data

def replay_events(events: Sequence[V2Event]) -> Dict[str, Any]:
    """
    Deterministically replay a sequence of events into a dict.
    Events are sorted by (ts, event_id) before fold.
    """
    events_sorted = sorted(events, key=lambda e: (e.ts, e.event_id))
    data = {}
    for e in events_sorted:
        if e.event_id not in data:
            data[e.event_id] = e.payload
    return data

def replay_state_hash(events: Sequence[V2Event]) -> str:
    data = replay_events(events)
    return hash_snapshot(data)
