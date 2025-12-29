from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass(frozen=True)
class CommandMeta:
    command_id: UUID
    created_at: datetime
    source: str

@dataclass(frozen=True)
class BaseCommand:
    meta: CommandMeta
