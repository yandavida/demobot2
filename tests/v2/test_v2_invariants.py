from core.v2.models import V2Event, hash_payload
from core.v2.event_store import InMemoryEventStore
from core.v2.orchestrator import V2RuntimeOrchestrator
from core.v2.replay import replay_events, replay_state_hash
from datetime import datetime, timedelta

def make_event(event_id, session_id, ts, type, payload):
    return V2Event(
        event_id=event_id,
        session_id=session_id,
        ts=ts,
        type=type,
        payload=payload,
        payload_hash=hash_payload(payload),
    )

def test_determinism():
    store = InMemoryEventStore()
    orch = V2RuntimeOrchestrator(store)
    session_id = "sess1"
    base_ts = datetime(2025, 1, 1, 12, 0, 0)
    events = [
        make_event(f"e{i}", session_id, base_ts + timedelta(seconds=i), "QUOTE_INGESTED", {"val": i})
        for i in range(3)
    ]
    for e in events:
        orch.ingest_event(e)
    snap1 = orch.build_snapshot(session_id)
    snap2 = orch.build_snapshot(session_id)
    assert snap1.state_hash == snap2.state_hash
    assert snap1.data == snap2.data

def test_idempotency():
    store = InMemoryEventStore()
    orch = V2RuntimeOrchestrator(store)
    session_id = "sess2"
    ts = datetime(2025, 1, 1, 13, 0, 0)
    e = make_event("evt1", session_id, ts, "QUOTE_INGESTED", {"foo": 1})
    state1 = orch.ingest_event(e)
    state2 = orch.ingest_event(e)  # duplicate
    assert state2.version == state1.version  # version increments only once
    assert len(state2.applied) == 1
    snap = orch.build_snapshot(session_id)
    snap2 = orch.build_snapshot(session_id)
    assert snap.state_hash == snap2.state_hash

def test_replayability():
    store = InMemoryEventStore()
    orch = V2RuntimeOrchestrator(store)
    session_id = "sess3"
    base_ts = datetime(2025, 1, 1, 14, 0, 0)
    events = [
        make_event(f"e{i}", session_id, base_ts + timedelta(seconds=i), "QUOTE_INGESTED", {"val": i})
        for i in range(5)
    ]
    for e in events:
        orch.ingest_event(e)
    snap = orch.build_snapshot(session_id)
    store_events = store.list(session_id)
    replayed = replay_events(store_events)
    assert snap.data == replayed
    assert snap.state_hash == replay_state_hash(store_events)

def test_deterministic_ordering():
    store = InMemoryEventStore()
    orch = V2RuntimeOrchestrator(store)
    session_id = "sess4"
    ts = datetime(2025, 1, 1, 15, 0, 0)
    e1 = make_event("a", session_id, ts, "QUOTE_INGESTED", {"foo": 1})
    e2 = make_event("b", session_id, ts, "QUOTE_INGESTED", {"foo": 2})
    # Ingest in reverse order
    orch.ingest_event(e2)
    orch.ingest_event(e1)
    snap1 = orch.build_snapshot(session_id)
    # Ingest in forward order in a new orchestrator
    store2 = InMemoryEventStore()
    orch2 = V2RuntimeOrchestrator(store2)
    orch2.ingest_event(e1)
    orch2.ingest_event(e2)
    snap2 = orch2.build_snapshot(session_id)
    assert snap1.state_hash == snap2.state_hash
    assert snap1.data == snap2.data
