
from core.v2.event_store_sqlite import SqliteEventStore
from core.v2.snapshot_store_sqlite import SqliteSnapshotStore
from core.v2.session_store_sqlite import SqliteSessionStore
from core.v2.persistence_config import get_v2_db_path
from core.v2.orchestrator import V2RuntimeOrchestrator
from core.v2.snapshot_policy import EveryNSnapshotPolicy
from core.v2.models import EventType, Snapshot, V2Event, hash_payload
import uuid
from datetime import datetime
from typing import Any, Tuple
from core.validation.error_envelope import ErrorEnvelope


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
            from api.v2.http_errors import not_found

            not_found("session_not_found", "Session not found")

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
        # Enforce replay-only for SNAPSHOT compute requests: if a compute
        # request references a `market_snapshot_id` it must already be
        # persisted in the artifact store. This prevents any provider
        # fallback at compute time and guarantees deterministic replay.
        if type == "COMPUTE_REQUESTED" and isinstance(payload, dict) and payload.get("kind") == "SNAPSHOT":
            params = payload.get("params") if isinstance(payload.get("params"), dict) else {}
            msid = params.get("market_snapshot_id")
            # allow the all-zero sentinel id used by tests as a no-op placeholder
            if msid is not None and msid != ("0" * 64):
                try:
                    # Lazy import to avoid import cycles in tests
                    from core.market_data.artifact_store import get_market_snapshot
                    # validate market requirements (Gate M3) before compute/pricing
                    from core.market_data.validate_requirements import validate_market_requirements
                    from core.commands.compute_request_command import ComputeRequestPayload

                    # will raise ValueError carrying an ErrorEnvelope-like dict when missing
                    snapshot = get_market_snapshot(msid)

                    # Construct a minimal ComputeRequestPayload dataclass for validation
                    req_payload = ComputeRequestPayload(kind=payload.get("kind"), params=params)
                    err = validate_market_requirements(req_payload, snapshot)
                    if err is not None:
                        # semantic errors map to HTTP 422 per Gate B contract
                        from api.v2.http_errors import raise_http

                        raise_http(err, 422)
                except ValueError as e:
                    detail = e.args[0] if e.args else {"detail": "market snapshot not found"}
                    # If the ValueError carries an envelope/dict use raise_http, otherwise map to not_found
                    from api.v2.http_errors import raise_http, not_found

                    if isinstance(detail, dict):
                        raise_http(detail, 404)
                    else:
                        not_found("market_snapshot_not_found", str(detail))
        eid = event_id or uuid.uuid4().hex
        # Deterministic replay requires canonical, caller-supplied event.ts (ADR-014 / Gate D).
        if ts is None:
            raise ValueError(
                ErrorEnvelope(
                    category="VALIDATION",
                    code="MISSING_EVENT_TS",
                    message="event.ts is required for deterministic ingestion",
                    details={"field": "ts"},
                )
            )
        event_ts = ts
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
        """
        Returns a materialized snapshot view: always includes all applied events up to latest version.
        Does NOT persist a new snapshot on read.
        """
        self._require_session(session_id)
        state = self.orchestrator.recover(session_id)
        from core.v2.models import hash_snapshot, Snapshot
        data = {}
        # סדר דטרמיניסטי
        for eid in sorted(state.applied.keys()):
            # state.applied: event_id -> version
            # state.data: event_id -> payload
            data[eid] = state.data[eid] if hasattr(state, 'data') and eid in getattr(state, 'data', {}) else None
        version = state.version
        state_hash = hash_snapshot(data)
        from datetime import datetime
        snap = Snapshot(
            session_id=session_id,
            version=version,
            created_at=datetime.utcnow(),  # לא רלוונטי לחוזה, רק פורמלי
            state_hash=state_hash,
            data=data,
        )
        return snap

# Singleton instance for router import
