from core.v2.models import V2Event
from typing import List

def stable_sort_events(events: List[V2Event]) -> List[V2Event]:
    """ממיין אירועים בסדר דטרמיניסטי: (ts, event_id)"""
    return sorted(events, key=lambda e: (e.ts, e.event_id))
