from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SessionLimits:
    ttl_seconds: int = 3600
    max_snapshots: int = 500
    max_events: int = 10_000
    session_idle_expiry_seconds: int = 7200


__all__ = ["SessionLimits"]
