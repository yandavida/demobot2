from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Mapping, MutableMapping, Optional, Sequence, cast


Currency = Literal["ILS", "USD"]


@dataclass(frozen=True, init=False)
class Money:
    amount: float
    ccy: Currency

    def __init__(self, amount: float, ccy: Currency | str | None = None, currency: Currency | str | None = None) -> None:
        if ccy is None and currency is None:
            raise TypeError("Either ccy or currency must be provided.")
        if ccy is not None and currency is not None:
            raise TypeError("Specify only one of ccy or currency.")

        resolved_currency_input = ccy if ccy is not None else currency
        resolved_currency = cast(Currency, resolved_currency_input)
        assert resolved_currency is not None
        object.__setattr__(self, "amount", amount)
        object.__setattr__(self, "ccy", resolved_currency)

    def __str__(self) -> str:
        return f"{self.amount} {self.ccy}"

    @property
    def currency(self) -> Currency:
        return self.ccy

    @classmethod
    def zero(cls, ccy: Currency) -> "Money":
        return cls(amount=0.0, ccy=ccy)


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
    base_currency: str = "USD"
    cash_balances: MutableMapping[str, float] = field(default_factory=dict)

    def with_position(self, position: Position) -> "Portfolio":
        positions = list(self.positions) + [position]
        return Portfolio(positions=positions, base_currency=self.base_currency, cash_balances=dict(self.cash_balances))
