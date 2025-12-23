from core.v2.event_store_sqlite import SqliteEventStore
from core.v2.snapshot_store_sqlite import SqliteSnapshotStore
from core.v2.persistence_config import V2_DB_PATH
from core.v2.orchestrator import V2RuntimeOrchestrator
from core.v2.snapshot_policy import EveryNSnapshotPolicy
from core.v2.models import EventType, Snapshot, V2Event, hash_payload
from fastapi import HTTPException
import uuid
from datetime import datetime
from typing import Any, Tuple

class V2ServiceSqlite:
    def __init__(self, db_path: str = V2_DB_PATH):
        self.event_store = SqliteEventStore(db_path)
        self.snapshot_store = SqliteSnapshotStore(db_path)
        self.snapshot_policy = EveryNSnapshotPolicy(3)
        self.orchestrator = V2RuntimeOrchestrator(
            self.event_store,
            self.snapshot_store,
            self.snapshot_policy,
        )
        self._sessions: set[str] = set()
        self._seen_event_ids: dict[str, set[str]] = {}

    def create_session(self) -> str:
        sid = uuid.uuid4().hex
        self._sessions.add(sid)
        self._seen_event_ids[sid] = set()
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
        applied = self.event_store.append(event)
        if not pre_exists:
            seen.add(eid)
        state = self.orchestrator.ingest_event(event)
        return state.version, applied

    def get_snapshot(self, session_id: str) -> Snapshot:
        self._require_session(session_id)
        return self.orchestrator.build_snapshot(session_id)
