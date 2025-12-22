from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from core.portfolio.models import Currency


AssetId = str


@dataclass(frozen=True)
class PriceQuote:
    asset: AssetId
    price: float
    currency: Currency

    def __post_init__(self) -> None:  # type: ignore[override]
        if not (self.price > 0):
            raise ValueError(f"PriceQuote.price must be > 0, got {self.price}")


@dataclass(frozen=True)
class FxRateQuote:
    pair: str
    rate: float

    def __post_init__(self) -> None:  # type: ignore[override]
        if not (self.rate > 0):
            raise ValueError(f"FxRateQuote.rate must be > 0, got {self.rate}")


@dataclass(frozen=True)
class MarketSnapshot:
    quotes: Tuple[PriceQuote, ...] = field(default_factory=tuple)
    fx_rates: Tuple[FxRateQuote, ...] = field(default_factory=tuple)
    as_of: str | None = None

    def __post_init__(self) -> None:  # type: ignore[override]
        # Ensure deterministic ordering by asset / pair string
        sorted_quotes = tuple(sorted(self.quotes, key=lambda q: str(q.asset)))
        object.__setattr__(self, "quotes", sorted_quotes)
        sorted_fx = tuple(sorted(self.fx_rates, key=lambda f: str(f.pair)))
        object.__setattr__(self, "fx_rates", sorted_fx)


__all__ = ["AssetId", "PriceQuote", "FxRateQuote", "MarketSnapshot"]
