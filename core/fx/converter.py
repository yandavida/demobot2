from __future__ import annotations

from dataclasses import dataclass

from core.fx.provider import FxRateProvider
from core.portfolio.models import Currency, Money


@dataclass(frozen=True)
class FxConverter:
    provider: FxRateProvider
    base_ccy: Currency = "ILS"

    def to_base(self, money: Money) -> Money:
        if money.ccy == self.base_ccy:
            return money

        rate = self.provider.get(from_ccy=money.ccy, to_ccy=self.base_ccy)
        return Money(amount=money.amount * rate, ccy=self.base_ccy)
