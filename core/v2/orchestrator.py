
from __future__ import annotations
from core.v2.models import V2Event, SessionState, Snapshot, hash_snapshot, AppliedEvent
from core.v2.event_store import EventStore
from core.v2.snapshot_store import SnapshotStore
from core.v2.snapshot_policy import SnapshotPolicy
from core.v2.event_ordering import stable_sort_events
from datetime import datetime
from typing import Optional
import logging
import time

class V2RuntimeOrchestrator:
    """
    Orchestrates event ingestion and snapshot building for a session.
    - All events are appended to the store (including duplicates)
    - Session state (applied, version) is updated only on first application of an event_id
    - build_snapshot uses bounded replay from latest snapshot if available
    - Maintains applied_log[session_id]: list[AppliedEvent]
    """

    from typing import overload, Literal

    @overload
    def replay(self, session_id: str, return_start_version: Literal[False] = False) -> SessionState: ...
    @overload
    def replay(self, session_id: str, return_start_version: Literal[True]) -> tuple[int, SessionState]: ...
    def replay(self, session_id: str, return_start_version: bool = False):
        """
        Internal: For test instrumentation only. Replays session and returns (replay_start_version, SessionState).
        """
        base = None
        replay_start_version = 0
        if self.snapshot_store is not None:
            base = self.snapshot_store.latest(session_id)
        if base is not None:
            replay_start_version = base.version
        state = self.recover(session_id)
        if return_start_version:
            return replay_start_version, state
        return state
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

    def recover(self, session_id: str) -> SessionState:
        """
        Load latest snapshot and replay only tail events for session_id.
        Guarantees deterministic state after crash/restart.
        """
        base = None
        if self.snapshot_store is not None:
            base = self.snapshot_store.latest(session_id)
        if base is not None:
            # Load tail events after snapshot.version
            tail_events = self.store.list_after_version(session_id, base.version)
            data = dict(base.data)
            seen = set(base.data.keys())
            version = base.version
            applied = dict((eid, i+1) for i, eid in enumerate(sorted(seen)))
            applied_log = []
            for e in sorted(tail_events, key=lambda e: (e.ts, e.event_id)):
                if e.event_id not in seen:
                    data[e.event_id] = e.payload
                    version += 1
                    applied[e.event_id] = version
                    applied_log.append(AppliedEvent(event=e, state_version=version, applied_at=e.ts))
            state = SessionState(session_id=session_id, version=version, applied=applied)
            self._session_states[session_id] = state
            self._applied_log[session_id] = applied_log
            return state
        else:
            # No snapshot: replay all events
            events = self.store.list(session_id)
            data = {}
            seen = set()
            version = 0
            applied = {}
            applied_log = []
            for e in sorted(events, key=lambda e: (e.ts, e.event_id)):
                if e.event_id not in seen:
                    data[e.event_id] = e.payload
                    version += 1
                    applied[e.event_id] = version
                    applied_log.append(AppliedEvent(event=e, state_version=version, applied_at=e.ts))
            state = SessionState(session_id=session_id, version=version, applied=applied)
            self._session_states[session_id] = state
            self._applied_log[session_id] = applied_log
            return state

    def ingest_event(self, event: V2Event) -> SessionState:
        state = self._session_states.get(event.session_id)
        applied_log = self._applied_log.setdefault(event.session_id, [])
        if state is None:
            state = SessionState(session_id=event.session_id, version=0, applied={})
        snapshot_store = self.snapshot_store
        snapshot_policy = self.snapshot_policy
        last_snapshot_version = None
        if snapshot_store is not None:
            last_snapshot = snapshot_store.latest(event.session_id)
            if last_snapshot is not None:
                last_snapshot_version = last_snapshot.version
        if event.event_id not in state.applied:
            self.store.append(event)
            new_applied = dict(state.applied)
            new_version = state.version + 1
            new_applied[event.event_id] = new_version
            state = SessionState(session_id=event.session_id, version=new_version, applied=new_applied)
            applied_event = AppliedEvent(event=event, state_version=new_version, applied_at=datetime.utcnow())
            applied_log.append(applied_event)
            self._session_states[event.session_id] = state
            # Snapshot cadence policy integration
            if snapshot_store is not None and snapshot_policy is not None:
                should_snap, target_version = snapshot_policy.should_snapshot(
                    event.session_id,
                    last_snapshot_version,
                    new_version,
                )
                if should_snap and target_version == new_version:
                    # Build and persist snapshot at this version
                    snap = self.build_snapshot(event.session_id)
                    # build_snapshot will persist if policy allows, but we want to guarantee it here
                    snapshot_store.save(snap)
            return state
        else:
            # Idempotent: do not append duplicate event, do not increment version
            self._session_states[event.session_id] = state
            return state

    def build_snapshot(self, session_id: str) -> Snapshot:
        # Always use EventStore + SnapshotStore, never _applied_log/_session_states for correctness
        logger = logging.getLogger("core.v2.orchestrator")
        t0 = time.perf_counter()
        base = None
        mode = "full"
        base_version = 0
        tail_len = 0
        if self.snapshot_store is not None:
            base = self.snapshot_store.latest(session_id)
        if base is not None:
            all_events = self.store.list(session_id)
            if all_events:
                max_seq = len({e.event_id for e in all_events})
                if base.version == max_seq:
                    return base
                if base.version > max_seq:
                    raise ValueError(f"Snapshot version {base.version} > latest event version {max_seq}")
            mode = "delta"
            base_version = base.version
            tail_events = self.store.list_after_version(session_id, base.version)
            tail_len = len(tail_events)
            snap = self._build_snapshot_delta(session_id, base)
        else:
            snap = self._build_snapshot_full(session_id)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.debug(
            "build_snapshot: mode=%s session_id=%s base_version=%d tail_len=%d final_version=%d elapsed_ms=%.2f",
            mode, session_id, base_version, tail_len, snap.version, elapsed_ms
        )
        return snap
