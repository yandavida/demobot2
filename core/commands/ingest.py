from dataclasses import dataclass
from core.commands.base import BaseCommand

@dataclass(frozen=True)
class IngestQuoteCommand(BaseCommand):
    symbol: str
    price: float
    currency: str
    as_of: str
