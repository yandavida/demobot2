import pytest
from datetime import datetime
from core.v2.models import V2Event
from core.v2.orchestrator import V2RuntimeOrchestrator
from core.v2.event_store import InMemoryEventStore
from core.v2.snapshot_store import InMemorySnapshotStore
from tests.v2._canon import canonical_json_dumps, hash_canonical
from tests.v2._event_gen import generate_events, shuffle_events, with_duplicate_event_id

BASE_TS = datetime(2020, 1, 1, 12, 0, 0)

@pytest.mark.parametrize("n", [1, 2, 3, 10, 50, 200, 500])
def test_replay_same_events_same_hash(n):
    events = generate_events(n, seed=42, base_ts=BASE_TS)
    store = InMemoryEventStore()
    orchestrator = V2RuntimeOrchestrator(store)
    for e in events:
        store.append(e)
    snap1 = orchestrator.build_snapshot("sess-1")
    # replay again
    store2 = InMemoryEventStore()
    orchestrator2 = V2RuntimeOrchestrator(store2)
    for e in events:
        store2.append(e)
    snap2 = orchestrator2.build_snapshot("sess-1")
    assert snap1.state_hash == snap2.state_hash
    assert snap1.version == snap2.version

@pytest.mark.parametrize("n", [3, 10, 50, 200])
def test_replay_permutation_invariance_same_hash(n):
    events = generate_events(n, seed=123, base_ts=BASE_TS)
    store = InMemoryEventStore()
    orchestrator = V2RuntimeOrchestrator(store)
    for e in events:
        store.append(e)
    snap1 = orchestrator.build_snapshot("sess-1")
    # shuffle
    events_shuffled = shuffle_events(events, seed=999)
    store2 = InMemoryEventStore()
    orchestrator2 = V2RuntimeOrchestrator(store2)
    for e in events_shuffled:
        store2.append(e)
    snap2 = orchestrator2.build_snapshot("sess-1")
    assert snap1.state_hash == snap2.state_hash
    assert snap1.version == snap2.version

def test_replay_duplicate_event_id_is_idempotent():
    events = generate_events(10, seed=7, base_ts=BASE_TS)
    events_dup = with_duplicate_event_id(events, pick_index=3)
    store = InMemoryEventStore()
    orchestrator = V2RuntimeOrchestrator(store)
    for e in events_dup:
        store.append(e)
    snap = orchestrator.build_snapshot("sess-1")
    # replay only unique
    store2 = InMemoryEventStore()
    orchestrator2 = V2RuntimeOrchestrator(store2)
    for e in events:
        store2.append(e)
    snap2 = orchestrator2.build_snapshot("sess-1")
    assert snap.state_hash == snap2.state_hash
    assert snap.version == snap2.version

def test_replay_same_timestamp_uses_stable_tiebreaker():
    from dataclasses import replace
    n = 10
    base_ts = BASE_TS
    events = generate_events(n, seed=5, base_ts=base_ts)
    # צור רשימה חדשה עם אותו timestamp לכל האירועים
    events = [replace(e, ts=base_ts) for e in events]
    store = InMemoryEventStore()
    orchestrator = V2RuntimeOrchestrator(store)
    for e in events:
        store.append(e)
    snap = orchestrator.build_snapshot("sess-1")
    # shuffle and replay
    events_shuffled = shuffle_events(events, seed=77)
    store2 = InMemoryEventStore()
    orchestrator2 = V2RuntimeOrchestrator(store2)
    for e in events_shuffled:
        store2.append(e)
    snap2 = orchestrator2.build_snapshot("sess-1")
    assert snap.state_hash == snap2.state_hash
    assert snap.version == snap2.version

def test_payload_equivalent_json_order_does_not_change_hash():
    # two events with same keys, different order
    ts = BASE_TS
    e1 = V2Event(event_id="evt-1", session_id="sess-1", ts=ts, type="QUOTE_INGESTED", payload={"a":1,"b":2}, payload_hash="")
    e2 = V2Event(event_id="evt-2", session_id="sess-1", ts=ts, type="QUOTE_INGESTED", payload={"b":2,"a":1}, payload_hash="")
    store = InMemoryEventStore()
    orchestrator = V2RuntimeOrchestrator(store)
    store.append(e1)
    store.append(e2)
    snap = orchestrator.build_snapshot("sess-1")
    # replay with reversed order
    store2 = InMemoryEventStore()
    orchestrator2 = V2RuntimeOrchestrator(store2)
    store2.append(e2)
    store2.append(e1)
    snap2 = orchestrator2.build_snapshot("sess-1")
    assert snap.state_hash == snap2.state_hash
    assert snap.version == snap2.version

@pytest.mark.parametrize("n", [1,2,3,10,50,200,500])
def test_replay_invariants_across_sizes(n):
    events = generate_events(n, seed=101, base_ts=BASE_TS)
    store = InMemoryEventStore()
    orchestrator = V2RuntimeOrchestrator(store)
    for e in events:
        store.append(e)
    snap = orchestrator.build_snapshot("sess-1")
    # shuffle and replay
    events_shuffled = shuffle_events(events, seed=202)
    store2 = InMemoryEventStore()
    orchestrator2 = V2RuntimeOrchestrator(store2)
    for e in events_shuffled:
        store2.append(e)
    snap2 = orchestrator2.build_snapshot("sess-1")
    assert snap.state_hash == snap2.state_hash
    assert snap.version == snap2.version
