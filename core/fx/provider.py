from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from core.portfolio.models import Currency


@dataclass(frozen=True)
class FxRateProvider:
    rates: Mapping[str, float]

    @classmethod
    def from_usd_ils(cls, usd_ils: float) -> "FxRateProvider":
        return cls(rates={"USD/ILS": usd_ils, "ILS/USD": 1 / usd_ils})

    def get(self, from_ccy: Currency, to_ccy: Currency) -> float:
        if from_ccy == to_ccy:
            return 1.0

        pair = f"{from_ccy}/{to_ccy}"
        try:
            return self.rates[pair]
        except KeyError as exc:
            raise ValueError(f"Unsupported FX pair: {pair}") from exc
