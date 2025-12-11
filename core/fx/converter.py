from __future__ import annotations

from dataclasses import dataclass

from core.fx.contracts import normalize_currency
from core.fx.provider import FxRateProvider
from core.portfolio.models import Currency, Money


@dataclass(frozen=True)
class FxConverter:
    provider: FxRateProvider
    base_ccy: Currency = "ILS"

    def __post_init__(self) -> None:
        normalized_base = normalize_currency(self.base_ccy)
        object.__setattr__(self, "base_ccy", normalized_base)

    def convert(self, money: Money, to_ccy: Currency) -> Money:
        target_ccy = normalize_currency(to_ccy)

        if money.ccy == target_ccy:
            return money

        rate = self.provider.get(money.ccy, target_ccy)
        return Money(amount=money.amount * rate, ccy=target_ccy)

    def to_base(self, money: Money) -> Money:
        return self.convert(money, self.base_ccy)
