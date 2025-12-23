from __future__ import annotations

from datetime import datetime
from typing import Any, Tuple
import uuid
from fastapi import HTTPException
from core.v2.event_store import InMemoryEventStore
from core.v2.models import EventType, Snapshot, V2Event, hash_payload
from core.v2.orchestrator import V2RuntimeOrchestrator
from core.v2.snapshot_policy import EveryNSnapshotPolicy
from core.v2.snapshot_store import InMemorySnapshotStore



# -----------------------------
# Test-only hooks (module scope)
# -----------------------------
_FORCE_RAISE_FOR_TESTS: bool = False

def enable_force_raise_for_tests(flag: bool) -> None:
    global _FORCE_RAISE_FOR_TESTS
    _FORCE_RAISE_FOR_TESTS = flag

def reset_for_tests() -> None:
    global _FORCE_RAISE_FOR_TESTS, v2_service
    _FORCE_RAISE_FOR_TESTS = False
    v2_service = V2Service()
    if hasattr(v2_service, '_seen_event_ids'):
        v2_service._seen_event_ids.clear()

# -----------------------------
# V2 Service (clean runtime)
# -----------------------------
class V2Service:
    def __init__(self) -> None:
        self.event_store = InMemoryEventStore()
        self.snapshot_store = InMemorySnapshotStore()
        self.snapshot_policy = EveryNSnapshotPolicy(3)
        self.orchestrator = V2RuntimeOrchestrator(
            self.event_store,
            self.snapshot_store,
            self.snapshot_policy,
        )
        self._sessions: set[str] = set()

    def create_session(self) -> str:
        if _FORCE_RAISE_FOR_TESTS:
            raise RuntimeError("forced error for tests")
        sid = uuid.uuid4().hex
        self._sessions.add(sid)
        return sid

    def _require_session(self, session_id: str) -> None:
        if session_id not in self._sessions:
            raise HTTPException(status_code=404, detail={"detail": "Session not found"})

    def ingest_event(
        self,
        session_id: str,
        *,
        event_id: str | None,
        ts: datetime | None,
        type: EventType,
        payload: dict[str, Any],
    ) -> Tuple[int, bool]:
        self._require_session(session_id)
        eid = event_id or uuid.uuid4().hex
        event_ts = ts or datetime.utcnow()
        # Track idempotency per session
        if not hasattr(self, '_seen_event_ids'):
            self._seen_event_ids = {}
        seen = self._seen_event_ids.setdefault(session_id, set())
        pre_exists = eid in seen
        payload_hash = hash_payload(payload)
        event = V2Event(
            event_id=eid,
            session_id=session_id,
            ts=event_ts,
            type=type,
            payload=payload,
            payload_hash=payload_hash,
        )
        state = self.orchestrator.ingest_event(event)
        if not pre_exists:
            seen.add(eid)
        applied = not pre_exists
        return state.version, applied

    def get_snapshot(self, session_id: str) -> Snapshot:
        self._require_session(session_id)
        return self.orchestrator.build_snapshot(session_id)

# -----------------------------
# Singleton
# -----------------------------
v2_service = V2Service()
