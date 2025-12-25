from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Literal
from datetime import datetime
import json
import hashlib

@dataclass(frozen=True)
class AppliedEvent:
    event: V2Event
    state_version: int
    applied_at: datetime


EventType = Literal[
    "QUOTE_INGESTED",
    "COMPUTE_REQUESTED",
    "SNAPSHOT_CREATED",
    "PORTFOLIO_CREATED",
    "PORTFOLIO_POSITION_UPSERTED",
    "PORTFOLIO_POSITION_REMOVED"
]

@dataclass(frozen=True)
class V2Event:
    event_id: str
    session_id: str
    ts: datetime
    type: EventType
    payload: Dict[str, Any]
    payload_hash: str

@dataclass(frozen=True)
class SessionState:
    session_id: str
    version: int
    applied: Dict[str, int] = field(default_factory=dict)  # event_id -> state_version

@dataclass(frozen=True)
class Snapshot:
    session_id: str
    version: int
    created_at: datetime
    state_hash: str
    data: Dict[str, Any]

# --- Canonical hashing utilities ---
def canonical_json(obj: Any) -> str:
    """Deterministic JSON serialization (sorted keys, no whitespace)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def hash_payload(payload: Dict[str, Any]) -> str:
    return sha256_hex(canonical_json(payload).encode("utf-8"))

def hash_snapshot(data: Dict[str, Any]) -> str:
    return sha256_hex(canonical_json(data).encode("utf-8"))
