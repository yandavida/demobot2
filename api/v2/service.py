from core.v2.event_store import InMemoryEventStore
from core.v2.snapshot_store import InMemorySnapshotStore
from core.v2.snapshot_policy import EveryNSnapshotPolicy
from core.v2.orchestrator import V2RuntimeOrchestrator
from core.v2.models import V2Event, hash_payload
from datetime import datetime
import uuid

class V2Service:
    def __init__(self):
        self.event_store = InMemoryEventStore()
        self.snapshot_store = InMemorySnapshotStore()
        self.snapshot_policy = EveryNSnapshotPolicy(3)
        self.orch = V2RuntimeOrchestrator(
            self.event_store, self.snapshot_store, self.snapshot_policy
        )
        self._sessions = set()

    def create_session(self) -> str:
        session_id = uuid.uuid4().hex
        self._sessions.add(session_id)
        return session_id

    def ingest_event(self, session_id: str, req) -> tuple[int, bool]:
        if session_id not in self._sessions:
            raise KeyError("Session not found")
        event_id = req.event_id or uuid.uuid4().hex
        ts = req.ts or datetime.utcnow()
        event = V2Event(
            event_id=event_id,
            session_id=session_id,
            ts=ts,
            type=req.type,
            payload=req.payload,
            payload_hash=hash_payload(req.payload),
        )
        state_before = self.orch._session_states.get(session_id)
        state = self.orch.ingest_event(event)
        applied = False
        if state_before is None or event_id not in state_before.applied:
            applied = True
        return state.version, applied

    def get_snapshot(self, session_id: str):
        if session_id not in self._sessions:
            raise KeyError("Session not found")
        return self.orch.build_snapshot(session_id)

    def reset_for_tests(self):
        self.__init__()

v2_service = V2Service()
