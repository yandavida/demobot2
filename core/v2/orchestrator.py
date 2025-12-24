from __future__ import annotations

from core.v2.models import V2Event, SessionState, Snapshot, hash_snapshot, AppliedEvent
from core.v2.event_store import EventStore
from core.v2.snapshot_store import SnapshotStore
from core.v2.snapshot_policy import SnapshotPolicy
from core.v2.event_ordering import stable_sort_events
from datetime import datetime
from typing import Optional

class V2RuntimeOrchestrator:
    """
    Orchestrates event ingestion and snapshot building for a session.
    - All events are appended to the store (including duplicates)
    - Session state (applied, version) is updated only on first application of an event_id
    - build_snapshot uses bounded replay from latest snapshot if available
    - Maintains applied_log[session_id]: list[AppliedEvent]
    """

    def _replay_events_into_data(self, base_data: dict, events: list[V2Event]) -> dict:
        data = dict(base_data)
        for e in stable_sort_events(events):
            if e.event_id not in data:
                data[e.event_id] = e.payload
        return data

    def _build_snapshot_full(self, session_id: str) -> Snapshot:
        events = self.store.list(session_id)
        events = stable_sort_events(events)
        data = {}
        seen = set()
        version = 0
        for e in events:
            if e.event_id not in seen:
                data[e.event_id] = e.payload
                seen.add(e.event_id)
                version += 1
        state_hash = hash_snapshot(data)
        now = datetime.utcnow()
        return Snapshot(
            session_id=session_id,
            version=version,
            created_at=now,
            state_hash=state_hash,
            data=data,
        )

    def _build_snapshot_delta(self, session_id: str, base: Snapshot) -> Snapshot:
        tail_events = self.store.list_after_version(session_id, base.version)
        data = self._replay_events_into_data(base.data, tail_events)
        # version = base.version + unique new event_ids in tail
        seen = set(base.data.keys())
        version = base.version
        for e in stable_sort_events(tail_events):
            if e.event_id not in seen:
                seen.add(e.event_id)
                version += 1
        state_hash = hash_snapshot(data)
        now = datetime.utcnow()
        return Snapshot(
            session_id=session_id,
            version=version,
            created_at=now,
            state_hash=state_hash,
            data=data,
        )
    def __init__(self, store: EventStore, snapshot_store: Optional[SnapshotStore] = None, snapshot_policy: Optional[SnapshotPolicy] = None):
        self.store = store
        self.snapshot_store = snapshot_store
        self.snapshot_policy = snapshot_policy
        self._session_states: dict[str, SessionState] = {}
        self._applied_log: dict[str, list[AppliedEvent]] = {}

    def ingest_event(self, event: V2Event) -> SessionState:
        self.store.append(event)
        state = self._session_states.get(event.session_id)
        applied_log = self._applied_log.setdefault(event.session_id, [])
        if state is None:
            state = SessionState(session_id=event.session_id, version=0, applied={})
        if event.event_id not in state.applied:
            new_applied = dict(state.applied)
            new_version = state.version + 1
            new_applied[event.event_id] = new_version
            state = SessionState(session_id=event.session_id, version=new_version, applied=new_applied)
            applied_event = AppliedEvent(event=event, state_version=new_version, applied_at=datetime.utcnow())
            applied_log.append(applied_event)
        self._session_states[event.session_id] = state
        return state

    def build_snapshot(self, session_id: str) -> Snapshot:
        # Always use EventStore + SnapshotStore, never _applied_log/_session_states for correctness
        base = None
        if self.snapshot_store is not None:
            base = self.snapshot_store.latest(session_id)
        if base is not None:
            snap = self._build_snapshot_delta(session_id, base)
        else:
            snap = self._build_snapshot_full(session_id)
        # Optionally save snapshot
        if self.snapshot_store is not None and self.snapshot_policy is not None:
            if self.snapshot_policy.should_snapshot(snap.version):
                self.snapshot_store.save(snap)
        return snap
