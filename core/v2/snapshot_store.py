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
    def list(self, session_id: str) -> list[Snapshot]:
        """החזר את כל הסנאפשוטים עבור session_id בסדר גרסאות עולה."""
        snaps = [snap for (sid, _), snap in self._store.items() if sid == session_id]
        return sorted(snaps, key=lambda s: s.version)
    def __init__(self) -> None:
        self._store: dict[tuple[str, int], Snapshot] = {}  # (session_id, version) -> Snapshot
        self._latest: dict[str, Snapshot] = {}  # session_id -> Snapshot

    def save(self, snapshot: Snapshot) -> None:
        key = (snapshot.session_id, snapshot.version)
        self._store[key] = snapshot
        self._latest[snapshot.session_id] = snapshot

    def get(self, session_id: str, version: int) -> Optional[Snapshot]:
        return self._store.get((session_id, version))

    def latest(self, session_id: str) -> Optional[Snapshot]:
        return self._latest.get(session_id)
