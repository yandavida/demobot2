"""
Canonical Money/Currency contract for all core layers.
"""
from dataclasses import dataclass
from typing import Literal
import math

Currency = Literal["ILS", "USD"]


def normalize_currency(value: Currency | str | None, field_name: str = "currency") -> Currency:
    if value is None:
        raise ValueError(f"{field_name} cannot be None")
    if isinstance(value, str):
        val = value.upper()
        if val not in ("ILS", "USD"):
            raise ValueError(f"Invalid currency: {val!r}")
        return val  # type: ignore
    if value in ("ILS", "USD"):
        return value
    raise TypeError(f"Invalid currency for {field_name}: {value!r}")

@dataclass(frozen=True, init=False)
class Money:
    amount: float
    ccy: Currency
    def __init__(self, amount: float, ccy: Currency = None, currency: Currency = None):
        if ccy is not None and currency is not None:
            raise TypeError("Specify only one of ccy or currency")
        object.__setattr__(self, 'amount', float(amount))
        if not math.isfinite(self.amount):
            raise ValueError(f"Money.amount must be a finite float, got {self.amount!r}")
        cur = ccy if ccy is not None else currency
        object.__setattr__(self, 'ccy', normalize_currency(cur))
    @classmethod
    def zero(cls, ccy: Currency) -> "Money":
        return cls(0.0, ccy=ccy)
    def __str__(self):
        return f"{self.amount} {self.ccy}"

__all__ = ["Currency", "Money", "normalize_currency"]
