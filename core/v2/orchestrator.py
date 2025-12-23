from __future__ import annotations

from core.v2.models import V2Event, SessionState, Snapshot, hash_snapshot, AppliedEvent
from core.v2.event_store import EventStore
from core.v2.snapshot_store import SnapshotStore
from core.v2.snapshot_policy import SnapshotPolicy
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
        state = self._session_states.get(session_id)
        version = state.version if state else 0
        now = datetime.utcnow()
        applied_log = self._applied_log.get(session_id, [])
        # Try to use latest snapshot for bounded replay
        base_snapshot = None
        base_version = 0
        base_data = {}
        if self.snapshot_store is not None:
            latest = self.snapshot_store.latest(session_id)
            if latest is not None:
                base_snapshot = latest
                base_version = latest.version
                base_data = dict(latest.data)
        # Get applied events after base_version
        tail = [ae for ae in applied_log if ae.state_version > base_version]
        # Replay from base_data
        data = dict(base_data)
        for ae in tail:
            if ae.event.event_id not in data:
                data[ae.event.event_id] = ae.event.payload
        state_hash = hash_snapshot(data)
        snap = Snapshot(
            session_id=session_id,
            version=version,
            created_at=now,
            state_hash=state_hash,
            data=data,
        )
        # Optionally save snapshot
        if self.snapshot_store is not None and self.snapshot_policy is not None:
            if self.snapshot_policy.should_snapshot(version):
                self.snapshot_store.save(snap)
        return snap
