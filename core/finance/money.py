from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping
import math
from core.finance.currency import Currency, normalize_currency

@dataclass(frozen=True, init=False)
class Money:
    amount: float
    ccy: Currency

    def __init__(
        self,
        amount: float,
        ccy: Currency | str | None = None,
        currency: Currency | str | None = None,
    ) -> None:
        if ccy is not None and currency is not None:
            raise TypeError("Specify only one of 'ccy' or 'currency'.")
        if ccy is None and currency is None:
            raise TypeError("Either 'ccy' or 'currency' must be provided.")
        raw_value = ccy if ccy is not None else currency
        resolved_ccy = normalize_currency(raw_value, field_name="Money.currency")
        if not isinstance(amount, float) or not math.isfinite(amount):
            raise ValueError("amount must be a finite float")
        object.__setattr__(self, "amount", amount)
        object.__setattr__(self, "ccy", resolved_ccy)

    def __str__(self) -> str:
        return f"{self.amount} {self.ccy}"

    def to_dict(self) -> dict[str, Any]:
        return {"amount": self.amount, "ccy": self.ccy}

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "Money":
        if not (isinstance(d, Mapping) and "amount" in d and "ccy" in d):
            raise ValueError("Invalid dict for Money: missing keys")
        amount = d["amount"]
        ccy = d["ccy"]
        if not isinstance(amount, float):
            raise ValueError("amount must be a float")
        return cls(amount=amount, ccy=ccy)

    @classmethod
    def zero(cls, ccy: Currency | str) -> "Money":
        return cls(amount=0.0, ccy=ccy)
