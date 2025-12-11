from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from core.fx.contracts import (
    Currency,
    FxRateProvider as FxRateProviderProtocol,
    normalize_currency,
)


@dataclass(frozen=True)
class FxRateProvider(FxRateProviderProtocol):
    """Concrete in-memory FX rate provider based on a mapping of pairs -> rates.

    Expectation:
        rates["USD/ILS"] = מספר השקלים לדולר אחד
        rates["ILS/USD"] = מספר הדולרים לשקל אחד
        וכן הלאה לזוגות נוספים.
    """

    rates: Mapping[str, float]

    @classmethod
    def from_usd_ils(cls, usd_ils: float) -> "FxRateProvider":
        """Convenience constructor for a simple USD/ILS universe."""
        # 1 USD = usd_ils ILS  →  1 ILS = 1 / usd_ils USD
        return cls(rates={"USD/ILS": usd_ils, "ILS/USD": 1 / usd_ils})

    def get(self, from_ccy: Currency | str, to_ccy: Currency | str) -> float:
        """Return FX rate such that: 1 from_ccy = rate * to_ccy."""
        base = normalize_currency(from_ccy)
        quote = normalize_currency(to_ccy)

        if base == quote:
            return 1.0

        pair = f"{base}/{quote}"
        try:
            return self.rates[pair]
        except KeyError as exc:
            raise ValueError(f"Unsupported FX pair: {pair}") from exc
