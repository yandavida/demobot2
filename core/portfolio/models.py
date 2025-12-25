from __future__ import annotations


from dataclasses import dataclass, field
from typing import Mapping, MutableMapping, Sequence

# Canonical finance primitives
from core.finance.currency import Currency, normalize_currency
from core.finance.money import Money
from core.market_data.types import MarketSnapshot

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
    cash_balances: MutableMapping[Currency, float] = field(default_factory=dict)

    def __post_init__(self):
        # Always normalize base_currency to canonical Currency
        object.__setattr__(self, "base_currency", normalize_currency(self.base_currency, field_name="Portfolio.base_currency"))

    def with_position(self, position: Position) -> "Portfolio":
        positions = list(self.positions) + [position]
        return Portfolio(
            positions=positions,
            base_currency=self.base_currency,
            cash_balances=dict(self.cash_balances),
        )

    def normalized_cash_balances(self) -> MutableMapping[Currency, float]:
        # Return a shallow copy to avoid exposing internal dict
        return dict(self.cash_balances)

    def normalized_base_currency(self) -> Currency:
        return normalize_currency(self.base_currency, field_name="Portfolio.base_currency")

__all__ = [
    "MarketSnapshot",
    "Position",
    "Portfolio",
    "Currency",
    "Money",
    "normalize_currency",
]
