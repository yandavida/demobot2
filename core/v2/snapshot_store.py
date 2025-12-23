from __future__ import annotations
from typing import Protocol, Optional
from core.v2.models import Snapshot

class SnapshotStore(Protocol):
    def save(self, snapshot: Snapshot) -> None:
        ...
    def get(self, session_id: str, version: int) -> Optional[Snapshot]:
        ...
    def latest(self, session_id: str) -> Optional[Snapshot]:
        ...

class InMemorySnapshotStore:
    def __init__(self) -> None:
        self._store = {}  # (session_id, version) -> Snapshot
        self._latest = {}  # session_id -> Snapshot

    def save(self, snapshot: Snapshot) -> None:
        key = (snapshot.session_id, snapshot.version)
        self._store[key] = snapshot
        self._latest[snapshot.session_id] = snapshot

    def get(self, session_id: str, version: int) -> Optional[Snapshot]:
        return self._store.get((session_id, version))

    def latest(self, session_id: str) -> Optional[Snapshot]:
        return self._latest.get(session_id)
