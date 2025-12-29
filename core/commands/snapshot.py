from dataclasses import dataclass
from core.commands.base import BaseCommand

@dataclass(frozen=True)
class SnapshotRequestCommand(BaseCommand):
    reason: str | None = None
