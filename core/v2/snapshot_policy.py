from __future__ import annotations

from typing import Optional, Tuple, Protocol

class SnapshotPolicy(Protocol):
    def should_snapshot(
        self,
        session_id: str,
        last_snapshot_version: Optional[int],
        next_applied_version: int,
        last_snapshot_created_at = None,
    ) -> Tuple[bool, Optional[int]]:
        ...

class EveryNSnapshotPolicy:
    def __init__(self, n: int = 50) -> None:
        self.n = n

    def should_snapshot(
        self,
        session_id: str,
        last_snapshot_version: Optional[int],
        next_applied_version: int,
        last_snapshot_created_at = None,
    ) -> Tuple[bool, Optional[int]]:
        """
        Decide if a snapshot should be created at next_applied_version.
        - Never snapshot at version 0.
        - If last_snapshot_version is None, first snapshot at N.
        - Otherwise, next snapshot at last_snapshot_version + N.
        """
        if next_applied_version == 0:
            return False, None
        if last_snapshot_version is None:
            if next_applied_version >= self.n:
                return next_applied_version % self.n == 0, next_applied_version if next_applied_version % self.n == 0 else None
            return False, None
        target = last_snapshot_version + self.n
        if next_applied_version == target:
            return True, target
        return False, None
