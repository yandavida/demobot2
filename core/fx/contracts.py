from __future__ import annotations

from typing import Protocol

from core.portfolio.models import Currency, Money


class FxRateProvider(Protocol):
    """Provides foreign exchange rates between two currencies."""

    def get_rate(self, base_currency: Currency, quote_currency: Currency) -> float:
        ...


class FxConverter(Protocol):
    """Converts monetary amounts between currencies."""

    def convert(self, money: Money, target_currency: Currency) -> Money:
        ...
