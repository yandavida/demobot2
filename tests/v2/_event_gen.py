import random
from datetime import datetime, timedelta
from typing import List
from core.v2.models import V2Event

def generate_events(n: int, seed: int, base_ts: datetime) -> List[V2Event]:
    rnd = random.Random(seed)
    events = []
    for i in range(n):
        ts = base_ts + timedelta(seconds=i)
        event_id = f"evt-{i}"
        payload = {"val": i, "rand": rnd.randint(0, 1000)}
        events.append(V2Event(
            event_id=event_id,
            session_id="sess-1",
            ts=ts,
            type="QUOTE_INGESTED",
            payload=payload,
            payload_hash="",
        ))
    return events

def shuffle_events(events, seed):
    rnd = random.Random(seed)
    events = list(events)
    rnd.shuffle(events)
    return events

def with_duplicate_event_id(events, pick_index=0):
    events = list(events)
    if events:
        events.append(events[pick_index])
    return events
