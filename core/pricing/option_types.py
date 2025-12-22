from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from core.portfolio.models import Currency


@dataclass(frozen=True)
class EuropeanOption:
    underlying: str
    option_type: Literal["call", "put"]
    strike: float
    expiry_t: float  # year fraction
    currency: Currency = "USD"
    contract_multiplier: float = 1.0
    vol: float | None = None


@dataclass(frozen=True)
class BsInputs:
    spot: float
    strike: float
    rate: float
    dividend_yield: float = 0.0
    vol: float = 0.0
    t: float = 0.0


__all__ = ["EuropeanOption", "BsInputs"]
