from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Mapping, Optional
import math
from core.finance.currency import Currency, normalize_currency
from core.finance.money import Money

@dataclass(frozen=True)
class FxRate:
    pair: str  # format "USD/ILS"
    rate: float  # quote per 1 base

    def __post_init__(self):
        if not isinstance(self.rate, float) or not math.isfinite(self.rate) or self.rate <= 0:
            raise ValueError("rate must be a finite float > 0")
        if not isinstance(self.pair, str) or len(self.pair) != 7 or self.pair[3] != "/":
            raise ValueError("pair must be in format 'AAA/BBB'")
        base, quote = self.pair[:3], self.pair[4:]
        if not (base.isalpha() and quote.isalpha() and base.isupper() and quote.isupper()):
            raise ValueError("pair must be uppercase 3-letter codes")

class FxRateProvider(Protocol):
    def get_rate(self, pair: str) -> Optional[float]:
        ...

class MappingFxRateProvider:
    def __init__(self, rates: Mapping[str, float]):
        self._rates = {k.upper(): float(v) for k, v in rates.items()}

    def get_rate(self, pair: str) -> Optional[float]:
        return self._rates.get(pair.upper())

class FxConverter:
    def __init__(self, provider: FxRateProvider):
        self.provider = provider

    def convert(self, amount: float, from_ccy: Currency, to_ccy: Currency) -> float:
        from_ccy = normalize_currency(from_ccy)
        to_ccy = normalize_currency(to_ccy)
        if from_ccy == to_ccy:
            return amount
        pair = f"{from_ccy}/{to_ccy}"
        rate = self.provider.get_rate(pair)
        if rate is not None:
            return amount * rate
        # Try inverse
        inv_pair = f"{to_ccy}/{from_ccy}"
        inv_rate = self.provider.get_rate(inv_pair)
        if inv_rate is not None and inv_rate > 0:
            return amount / inv_rate
        raise ValueError(f"FX rate not found for {from_ccy} to {to_ccy}")

    def convert_money(self, m: Money, to_ccy: Currency) -> Money:
        new_amount = self.convert(m.amount, m.ccy, to_ccy)
        return Money(amount=new_amount, ccy=to_ccy)
