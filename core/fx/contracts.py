from __future__ import annotations

from typing import Protocol, cast, get_args

from core.portfolio.models import Currency, Money


def normalize_currency(currency: Currency | str) -> Currency:
    """Normalize currency input to a supported ``Currency`` literal.

    ``Money`` accepts both ``Currency`` values and strings; this helper mirrors
    that flexibility while ensuring inputs are uppercased and validated against
    the supported currency literals.
    """

    supported_currencies = cast(tuple[str, ...], get_args(Currency))

    if isinstance(currency, str):
        normalized = currency.upper()
        if normalized not in supported_currencies:
            supported = ", ".join(supported_currencies)
            raise ValueError(
                f"Unsupported currency '{currency}'. Supported currencies: {supported}."
            )
        return cast(Currency, normalized)

    if currency not in supported_currencies:
        supported = ", ".join(supported_currencies)
        raise ValueError(
            f"Unsupported currency '{currency}'. Supported currencies: {supported}."
        )

    return currency


class FxRateProvider(Protocol):
    """Provides foreign exchange rates between two currencies."""

    def get(self, from_ccy: Currency, to_ccy: Currency) -> float:
        ...


class FxConverter(Protocol):
    """Converts monetary amounts between currencies."""

    def convert(self, money: Money, target_currency: Currency | str) -> Money:
        """Convert ``money`` to ``target_currency`` and return normalized ``Money``."""

        ...
