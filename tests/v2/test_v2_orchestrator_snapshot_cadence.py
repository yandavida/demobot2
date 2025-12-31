from core.v2.models import V2Event
from core.v2.orchestrator import V2RuntimeOrchestrator
from core.v2.snapshot_policy import EveryNSnapshotPolicy
from core.v2.snapshot_store import InMemorySnapshotStore
from core.v2.event_store import InMemoryEventStore

from datetime import datetime
def make_event(session_id, event_id, payload):
    return V2Event(
        session_id=session_id,
        event_id=event_id,
        ts=datetime(2025, 12, 31, 0, 0, 0),
        type="QUOTE_INGESTED",
        payload=payload,
        payload_hash="h",
    )

def test_orchestrator_snapshot_cadence():
    N = 3
    session_id = "s1"
    events = [make_event(session_id, f"e{i}", {"v": i}) for i in range(1, 7)]
    store = InMemoryEventStore()
    snap_store = InMemorySnapshotStore()
    policy = EveryNSnapshotPolicy(n=N)
    orch = V2RuntimeOrchestrator(store, snap_store, policy)
    for ev in events[:5]:
        orch.ingest_event(ev)
    snaps = snap_store.list(session_id)
    snap_versions = [s.version for s in snaps]
    assert snap_versions == [3], f"Expected snapshot at 3, got {snap_versions}"
    orch.ingest_event(events[5])
    snaps = snap_store.list(session_id)
    snap_versions = [s.version for s in snaps]
    assert snap_versions == [3,6], f"Expected snapshots at 3,6, got {snap_versions}"

def test_orchestrator_snapshot_determinism():
    N = 3
    session_id = "s2"
    events = [make_event(session_id, f"e{i}", {"v": i}) for i in range(1, 7)]
    # Run 1
    store1 = InMemoryEventStore()
    snap_store1 = InMemorySnapshotStore()
    orch1 = V2RuntimeOrchestrator(store1, snap_store1, EveryNSnapshotPolicy(n=N))
    for ev in events:
        orch1.ingest_event(ev)
    snaps1 = snap_store1.list(session_id)
    snap_versions1 = [s.version for s in snaps1]
    # Run 2
    store2 = InMemoryEventStore()
    snap_store2 = InMemorySnapshotStore()
    orch2 = V2RuntimeOrchestrator(store2, snap_store2, EveryNSnapshotPolicy(n=N))
    for ev in events:
        orch2.ingest_event(ev)
    snaps2 = snap_store2.list(session_id)
    snap_versions2 = [s.version for s in snaps2]
    assert snap_versions1 == snap_versions2 == [3,6], f"Determinism failed: {snap_versions1} vs {snap_versions2}"
