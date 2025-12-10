from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping, MutableMapping, Optional, Sequence


Currency = str


@dataclass(frozen=True)
class Money:
    amount: float
    ccy: Currency

    def __repr__(self) -> str:
        return f"Money(amount={self.amount}, ccy='{self.ccy}')"

    @property
    def currency(self) -> Currency:
        return self.ccy


@dataclass(frozen=True)
class MarketSnapshot:
    prices: Mapping[str, float]
    as_of: Optional[datetime] = None

    def get_price(self, symbol: str) -> Optional[float]:
        return self.prices.get(symbol)


@dataclass(frozen=True)
class Position:
    symbol: str
    quantity: float
    instrument_type: str = "equity"
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Portfolio:
    positions: Sequence[Position] = field(default_factory=list)
    base_currency: Currency = "USD"
    cash_balances: MutableMapping[str, float] = field(default_factory=dict)

    def with_position(self, position: Position) -> "Portfolio":
        positions = list(self.positions) + [position]
        return Portfolio(positions=positions, base_currency=self.base_currency, cash_balances=dict(self.cash_balances))
