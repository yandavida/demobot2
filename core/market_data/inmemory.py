from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence, Dict

from core.market_data.types import PriceQuote, FxRateQuote, MarketSnapshot
from core.market_data.errors import MissingQuoteError, MissingFxRateError


@dataclass(frozen=True)
class InMemoryMarketDataProvider:
    _prices: Dict[str, PriceQuote]
    _fx: Dict[str, FxRateQuote]
    _as_of: str | None

    def __init__(
        self,
        prices: Mapping[str, PriceQuote] | Sequence[PriceQuote] = (),
        fx_rates: Mapping[str, FxRateQuote] | Sequence[FxRateQuote] = (),
        as_of: str | None = None,
    ) -> None:
        # Normalize prices
        prices_dict: Dict[str, PriceQuote] = {}
        if isinstance(prices, Mapping):
            for k, v in prices.items():
                if not (v.price > 0):
                    raise ValueError("price must be > 0")
                prices_dict[str(k)] = v
        else:
            for v in prices:
                if not (v.price > 0):
                    raise ValueError("price must be > 0")
                prices_dict[str(v.asset)] = v

        fx_dict: Dict[str, FxRateQuote] = {}
        if isinstance(fx_rates, Mapping):
            for k, v in fx_rates.items():
                if not (v.rate > 0):
                    raise ValueError("fx rate must be > 0")
                fx_dict[str(k)] = v
        else:
            for v in fx_rates:
                if not (v.rate > 0):
                    raise ValueError("fx rate must be > 0")
                fx_dict[str(v.pair)] = v

        object.__setattr__(self, "_prices", prices_dict)
        object.__setattr__(self, "_fx", fx_dict)
        object.__setattr__(self, "_as_of", as_of)

    def get_price(self, asset: str) -> PriceQuote:
        k = str(asset)
        if k not in self._prices:
            raise MissingQuoteError(f"Price for {asset} not found")
        return self._prices[k]

    def has_price(self, asset: str) -> bool:
        return str(asset) in self._prices

    def get_fx_rate(self, pair: str) -> FxRateQuote:
        k = str(pair)
        if k not in self._fx:
            raise MissingFxRateError(f"FX rate for {pair} not found")
        return self._fx[k]

    def has_fx_rate(self, pair: str) -> bool:
        return str(pair) in self._fx

    def snapshot(self) -> MarketSnapshot:
        quotes = tuple(sorted(self._prices.values(), key=lambda q: str(q.asset)))
        fx_rates = tuple(sorted(self._fx.values(), key=lambda f: str(f.pair)))
        return MarketSnapshot(quotes=quotes, fx_rates=fx_rates, as_of=self._as_of)

    def with_updates(
        self,
        prices: Sequence[PriceQuote] = (),
        fx_rates: Sequence[FxRateQuote] = (),
        as_of: str | None = None,
    ) -> "InMemoryMarketDataProvider":
        # build merged maps (immutability: return new instance)
        new_prices: Dict[str, PriceQuote] = dict(self._prices)
        for p in prices:
            if not (p.price > 0):
                raise ValueError("price must be > 0")
            new_prices[str(p.asset)] = p

        new_fx: Dict[str, FxRateQuote] = dict(self._fx)
        for f in fx_rates:
            if not (f.rate > 0):
                raise ValueError("fx rate must be > 0")
            new_fx[str(f.pair)] = f

        return InMemoryMarketDataProvider(prices=new_prices, fx_rates=new_fx, as_of=as_of if as_of is not None else self._as_of)


__all__ = ["InMemoryMarketDataProvider"]
