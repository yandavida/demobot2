from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Mapping, MutableMapping, Optional, Sequence, TYPE_CHECKING

from core.models import Position as CorePosition

if TYPE_CHECKING:  # pragma: no cover - for type checkers only
    from core.fx.contracts import FxConverter


class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    ILS = "ILS"


@dataclass(frozen=True)
class Money:
    amount: float
    ccy: Currency

    def to(self, target_ccy: Currency, fx_converter: FxConverter | None = None) -> "Money":
        if target_ccy == self.ccy:
            return self
        if fx_converter is None:
            raise ValueError("FxConverter is required to convert Money to a different currency.")
        return fx_converter.convert(self, target_ccy)


@dataclass(frozen=True)
class MarketSnapshot:
    spot: Mapping[str, float]
    rates: Mapping[Currency, float] = field(default_factory=dict)
    iv: Mapping[str, float] = field(default_factory=dict)
    as_of: Optional[datetime] = None

    def get_spot(self, symbol: str) -> Optional[float]:
        return self.spot.get(symbol)


Position = CorePosition


@dataclass(frozen=True)
class Portfolio:
    positions: Sequence[Position] = field(default_factory=list)
    base_ccy: Currency = Currency.USD
    cash_balances: MutableMapping[Currency, float] = field(default_factory=dict)

    def with_position(self, position: Position) -> "Portfolio":
        positions = list(self.positions) + [position]
        return Portfolio(positions=positions, base_ccy=self.base_ccy, cash_balances=dict(self.cash_balances))
