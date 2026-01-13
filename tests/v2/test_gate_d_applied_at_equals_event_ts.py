from datetime import datetime
from core.v2.models import V2Event, hash_payload
from core.v2.event_store import InMemoryEventStore
from core.v2.orchestrator import V2RuntimeOrchestrator


def test_applied_event_applied_at_equals_event_ts():
    store = InMemoryEventStore()
    orch = V2RuntimeOrchestrator(store)
    session_id = "sess-gate-d"
    ts = datetime.fromisoformat("2025-01-01T00:00:00+00:00")
    ev = V2Event(event_id="evt-1", session_id=session_id, ts=ts, type="QUOTE_INGESTED", payload={"v":1}, payload_hash=hash_payload({"v":1}))
    orch.ingest_event(ev)
    applied_log = orch._applied_log[session_id]
    assert applied_log, "no applied events recorded"
    assert applied_log[-1].applied_at == ts
