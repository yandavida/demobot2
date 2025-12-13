from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, List, Protocol

from core.arbitrage.models import VenueQuote


class QuoteProvider(Protocol):
    """Abstract source of VenueQuote snapshots."""

    def get_quotes(self) -> Iterable[VenueQuote]:
        """Return the latest collection of quotes."""


@dataclass
class QuoteSnapshot:
    """Timestamped collection of venue quotes."""

    as_of: datetime
    quotes: List[VenueQuote]


@dataclass
class InMemoryQuoteFeed(QuoteProvider):
    """Simple in-memory feed for demo and tests."""

    quotes: List[VenueQuote] = field(default_factory=list)

    def update_quotes(self, quotes: Iterable[VenueQuote]) -> None:
        self.quotes = list(quotes)

    def get_quotes(self) -> Iterable[VenueQuote]:
        return list(self.quotes)
