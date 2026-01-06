from dataclasses import dataclass
from typing import Literal, Optional, Dict


@dataclass(frozen=True)
class SnapshotRequestPayload:
    force: bool = False


@dataclass(frozen=True)
class SnapshotRequestCommand:
    command_id: str
    session_id: str
    payload: SnapshotRequestPayload
    kind: Literal["SNAPSHOT_REQUEST"] = "SNAPSHOT_REQUEST"
    strict: bool = True
    meta: Optional[Dict[str, object]] = None
