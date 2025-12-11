from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FxRateProvider:
    usd_ils: float

    @classmethod
    def fixed(cls, usd_ils: float) -> "FxRateProvider":
        return cls(usd_ils=usd_ils)

    def get(self, pair: str) -> float:
        if pair == "USD/ILS":
            return self.usd_ils
        raise ValueError(f"Unsupported FX pair: {pair}")
