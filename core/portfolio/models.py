from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping, MutableMapping, Optional, Sequence


@dataclass(frozen=True)
class Currency:
    code: str

    def __hash__(self) -> int:
        return hash(self.code)

    def __str__(self) -> str:
        return self.code


@dataclass(frozen=True)
class Money:
    amount: float
    currency: str

    def __repr__(self) -> str:
        return f"Money(amount={self.amount}, currency='{self.currency}')"


@dataclass(frozen=True)
class MarketSnapshot:
    spot: Mapping[str, float]
    rates: Mapping[Currency, float] = field(default_factory=dict)
    iv: Mapping[str, float] = field(default_factory=dict)
    as_of: Optional[datetime] = None

    def get_price(self, symbol: str) -> Optional[float]:
        return self.spot.get(symbol)


@dataclass(frozen=True)
class Position:
    symbol: str
    quantity: float
    instrument_type: str = "equity"
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Portfolio:
    positions: Sequence[Position] = field(default_factory=list)
    base_currency: str = "USD"
    cash_balances: MutableMapping[str, float] = field(default_factory=dict)

    def with_position(self, position: Position) -> "Portfolio":
        positions = list(self.positions) + [position]
        return Portfolio(positions=positions, base_currency=self.base_currency, cash_balances=dict(self.cash_balances))
