from __future__ import annotations
from typing import Protocol

class SnapshotPolicy(Protocol):
    def should_snapshot(self, version: int) -> bool:
        ...

class EveryNSnapshotPolicy:
    def __init__(self, n: int) -> None:
        self.n = n
    def should_snapshot(self, version: int) -> bool:
        return version % self.n == 0 and version > 0
