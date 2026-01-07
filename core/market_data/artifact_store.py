from __future__ import annotations

from datetime import datetime

from core.market_data.market_snapshot_payload_v0 import MarketSnapshotPayloadV0
from core.market_data.identity import market_snapshot_id

from core.v2.event_store_sqlite import SqliteEventStore
from core.v2.models import V2Event, hash_payload
from core.v2.errors import EventConflictError

# Use the existing events table as an immutable artifact store.
# Rationale: the DB schema is sealed; reusing the events table under a
# dedicated session id avoids schema changes while providing idempotent
#, immutable storage semantics via the event_store append contract.
ARTIFACT_SESSION_ID = "__market_snapshot_artifacts__"


def put_market_snapshot(payload: MarketSnapshotPayloadV0) -> str:
    """Persist a market snapshot payload as an immutable artifact and return its id.

    - Id is computed using the canonical `market_snapshot_id` (SHA256 over canonical JSON).
    - Storage is idempotent: re-putting identical payload will not create duplicates.
    - Uses `events` table under a dedicated session id so no schema changes required.
    """
    msid = market_snapshot_id(payload)
    event_store = SqliteEventStore()
    payload_dict = payload.model_dump()
    ev = V2Event(
        event_id=msid,
        session_id=ARTIFACT_SESSION_ID,
        ts=datetime.fromisoformat("1970-01-01T00:00:00"),
        type="SNAPSHOT_CREATED",
        payload=payload_dict,
        payload_hash=hash_payload(payload_dict),
    )
    try:
        event_store.append(ev)
    except EventConflictError:
        # If the same id exists but with different payload, bubble up conflict.
        raise
    return msid


def get_market_snapshot(snapshot_id: str) -> MarketSnapshotPayloadV0:
    """Retrieve a previously stored snapshot payload by id.
    Raises MarketSnapshotNotFoundError when not found.
    The API layer will convert this to an ErrorEnvelope/HTTP error as needed.
    """
    event_store = SqliteEventStore()
    events = event_store.list(ARTIFACT_SESSION_ID)
    for e in events:
        if e.event_id == snapshot_id:
            return MarketSnapshotPayloadV0.model_validate(e.payload)
    from core.market_data.errors import MarketSnapshotNotFoundError

    raise MarketSnapshotNotFoundError(snapshot_id)
