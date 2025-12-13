from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class VenueQuote:
    """Simple quote container for a given venue.

    Attributes:
        venue: Name of the venue or broker.
        symbol: Instrument identifier.
        ccy: Currency of the quote (e.g., "USD", "ILS").
        bid: Best bid available at the venue.
        ask: Best ask available at the venue.
        size: Maximum executable size at the quoted levels (optional).
        fees_bps: Transaction cost in basis points applied on notional.
        latency_ms: Optional latency estimate for the venue quote.
    """

    venue: str
    symbol: str
    bid: float | None
    ask: float | None
    ccy: str = "USD"
    size: float | None = None
    fees_bps: float = 0.0
    latency_ms: float | None = None

    def has_liquidity(self) -> bool:
        """Return True if both sides are populated and tradable."""

        return self.bid is not None and self.ask is not None and self.bid > 0 and self.ask > 0


@dataclass(frozen=True)
class ArbitrageLeg:
    """Represents a buy/sell leg in a cross-venue arbitrage trade."""

    action: Literal["buy", "sell"]
    venue: str
    price: float
    quantity: float
    ccy: str = "USD"
    fees_bps: float = 0.0

    @property
    def notional(self) -> float:
        return self.price * self.quantity

    @property
    def fee_amount(self) -> float:
        return self.notional * (self.fees_bps / 10_000)


@dataclass
class ArbitrageOpportunity:
    """Container describing a cross-venue arbitrage opportunity."""

    symbol: str
    buy: ArbitrageLeg
    sell: ArbitrageLeg
    gross_edge: float
    net_edge: float
    edge_bps: float
    size: float
    ccy: str = "USD"
    notes: list[str] = field(default_factory=list)
    opportunity_id: str = ""
    as_of: datetime | None = None

    @property
    def expected_profit(self) -> float:
        """Expected absolute profit for the proposed size."""

        return self.net_edge * self.size


@dataclass
class ArbitrageConfig:
    """Configuration governing arbitrage search behavior."""

    min_edge_bps: float = 0.0
    min_size: float = 0.0
    allow_same_venue: bool = False
    default_size: float = 1.0
    max_latency_ms: float | None = None


__all__ = [
    "ArbitrageConfig",
    "ArbitrageLeg",
    "ArbitrageOpportunity",
    "VenueQuote",
]
