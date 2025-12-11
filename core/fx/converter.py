from __future__ import annotations

from dataclasses import dataclass

from core.fx.provider import FxRateProvider
from core.portfolio.models import Money


@dataclass(frozen=True)
class FxConverter:
    provider: FxRateProvider
    base_ccy: str = "ILS"

    def to_base(self, money: Money) -> Money:
        if money.ccy == self.base_ccy:
            return money

        if money.ccy == "USD" and self.base_ccy == "ILS":
            rate = self.provider.get("USD/ILS")
            return Money(amount=money.amount * rate, ccy="ILS")

        raise ValueError(
            f"Unsupported FX conversion from {money.ccy} to base currency {self.base_ccy}"
        )
