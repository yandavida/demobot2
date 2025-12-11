from __future__ import annotations

from dataclasses import dataclass

from core.fx.contracts import normalize_currency
from core.portfolio.models import Currency


@dataclass(frozen=True)
class FxRateProvider:
    usd_ils: float

    @classmethod
    def fixed(cls, usd_ils: float) -> "FxRateProvider":
        return cls(usd_ils=usd_ils)

    def get(self, base_currency: Currency | str, quote_currency: Currency | str) -> float:
        base = normalize_currency(base_currency)
        quote = normalize_currency(quote_currency)

        if base == quote:
            return 1.0

        if base == "USD" and quote == "ILS":
            return self.usd_ils

        if base == "ILS" and quote == "USD":
            return 1 / self.usd_ils

        raise ValueError(f"Unsupported FX pair: {base}/{quote}")
