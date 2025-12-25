from __future__ import annotations


from dataclasses import dataclass
from core.finance.currency import Currency


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

    quotes: tuple[PriceQuote, ...] = ()
    fx_rates: tuple[FxRateQuote, ...] = ()
    as_of: str | None = None

    def __post_init__(self):
        # מיון דטרמיניסטי
        object.__setattr__(self, "quotes", tuple(sorted(self.quotes, key=lambda q: q.asset)))
        object.__setattr__(self, "fx_rates", tuple(sorted(self.fx_rates, key=lambda f: f.pair)))

    def get_quote(self, asset: str) -> PriceQuote:
        for q in self.quotes:
            if q.asset == asset:
                return q
        raise KeyError(asset)

    def get_price(self, asset: str) -> float:
        return float(self.get_quote(asset).price)

__all__ = ["AssetId", "PriceQuote", "FxRateQuote", "MarketSnapshot"]
