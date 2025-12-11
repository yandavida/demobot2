from __future__ import annotations

from dataclasses import dataclass

from core.fx.contracts import FxRateProvider, normalize_currency
from core.portfolio.models import Currency, Money


@dataclass(frozen=True)
class FxConverter:
    provider: FxRateProvider
    base_ccy: Currency = "ILS"

    def __post_init__(self) -> None:
        normalized_base = normalize_currency(self.base_ccy)
        object.__setattr__(self, "base_ccy", normalized_base)

    def convert(self, money: Money, to_ccy: Currency | str) -> Money:
        """Convert a Money amount to the requested target currency."""
        target_ccy = normalize_currency(to_ccy)

        # אם המטבע כבר זהה – אין מה להמיר
        if money.ccy == target_ccy:
            return money

        rate = self.provider.get(money.ccy, target_ccy)
        return Money(amount=money.amount * rate, ccy=target_ccy)

    def to_base(self, money: Money) -> Money:
        """Convert a Money amount into the converter's base_ccy."""
        return self.convert(money, self.base_ccy)
