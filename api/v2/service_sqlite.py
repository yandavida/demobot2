
from core.v2.event_store_sqlite import SqliteEventStore
from core.v2.snapshot_store_sqlite import SqliteSnapshotStore
from core.v2.session_store_sqlite import SqliteSessionStore
from core.v2.persistence_config import get_v2_db_path
from core.v2.orchestrator import V2RuntimeOrchestrator
from core.v2.snapshot_policy import EveryNSnapshotPolicy
from core.v2.models import EventType, Snapshot, V2Event, hash_payload
from fastapi import HTTPException
import uuid
from datetime import datetime
from typing import Any, Tuple


# גלובלי עבור בדיקות
_FORCE_RAISE_FOR_TESTS = False

def enable_force_raise_for_tests(flag: bool = True):
    global _FORCE_RAISE_FOR_TESTS
    _FORCE_RAISE_FOR_TESTS = bool(flag)


# פונקציה לאיפוס סטייט עבור בדיקות
def reset_for_tests():
    global _FORCE_RAISE_FOR_TESTS
    _FORCE_RAISE_FOR_TESTS = False


class V2ServiceSqlite:
    def __init__(self, db_path: str = None):
        import logging
        if db_path is None:
            db_path = get_v2_db_path()
        self.event_store = SqliteEventStore(db_path)
        self.snapshot_store = SqliteSnapshotStore(db_path)
        self.session_store = SqliteSessionStore(db_path)
        self.snapshot_policy = EveryNSnapshotPolicy(3)
        self.orchestrator = V2RuntimeOrchestrator(
            self.event_store,
            self.snapshot_store,
            self.snapshot_policy,
        )
        self._sessions: set[str] = set()
        self._seen_event_ids: dict[str, set[str]] = {}
        logging.getLogger("api.v2.service_sqlite").debug(f"V2ServiceSqlite: db_path={db_path}")

    def close(self):
        if hasattr(self, 'event_store') and hasattr(self.event_store, 'close'):
            self.event_store.close()
        if hasattr(self, 'snapshot_store') and hasattr(self.snapshot_store, 'close'):
            self.snapshot_store.close()
        if hasattr(self, 'session_store') and hasattr(self.session_store, 'close'):
            self.session_store.close()
        self._sessions.clear()
        self._seen_event_ids.clear()

    def get_session(self, session_id: str):
        if self.session_store.exists(session_id):
            return {"session_id": session_id}
        return None

    def create_snapshot(self, session_id: str) -> Snapshot:
        self._require_session(session_id)
        snap = self.orchestrator.build_snapshot(session_id)
        self.snapshot_store.save(snap)
        return snap

    def create_session(self) -> str:
        sid = uuid.uuid4().hex
        now = datetime.utcnow()
        self.session_store.create(sid, now)
        self._sessions.add(sid)
        self._seen_event_ids[sid] = set()
        return sid

    def _require_session(self, session_id: str) -> None:
        if not self.session_store.exists(session_id):
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
        snap = self.snapshot_store.latest(session_id)
        if snap is not None:
            if getattr(snap, "state_hash", None):
                return snap
        built = self.orchestrator.build_snapshot(session_id)
        self.snapshot_store.put(built)
        snap_db = self.snapshot_store.latest(session_id)
        if snap_db is None or not getattr(snap_db, "state_hash", None):
            raise RuntimeError("Persisted snapshot missing state_hash")
        return snap_db

# Singleton instance for router import
