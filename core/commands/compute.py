from dataclasses import dataclass
from core.commands.base import BaseCommand

@dataclass(frozen=True)
class ComputeRequestCommand(BaseCommand):
    portfolio_id: str
    strict: bool = True
