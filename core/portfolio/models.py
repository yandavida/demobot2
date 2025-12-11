from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Mapping, MutableMapping, Optional, Sequence, cast


Currency = Literal["ILS", "USD"]


def _normalize_currency(value: Currency | str) -> Currency:
    return cast(Currency, value)


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
        resolved_currency = _normalize_currency(resolved_currency_input)
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


@dataclass(frozen=True, init=False)
class Portfolio:
    positions: Sequence[Position]
    base_currency: Currency
    cash_balances: MutableMapping[Currency, float]

    def __init__(
        self,
        positions: Sequence[Position] | None = None,
        base_currency: Currency | str = "USD",
        cash_balances: Mapping[Currency | str, float] | None = None,
    ) -> None:
        normalized_base_currency = _normalize_currency(base_currency)
        normalized_cash_balances: dict[Currency, float] = {
            _normalize_currency(ccy): amount for ccy, amount in (cash_balances or {}).items()
        }

        object.__setattr__(self, "positions", list(positions) if positions is not None else [])
        object.__setattr__(self, "base_currency", normalized_base_currency)
        object.__setattr__(self, "cash_balances", normalized_cash_balances)

    def with_position(self, position: Position) -> "Portfolio":
        positions = list(self.positions) + [position]
        return Portfolio(positions=positions, base_currency=self.base_currency, cash_balances=dict(self.cash_balances))
