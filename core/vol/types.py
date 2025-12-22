from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class VolKey:
    underlying: str
    expiry_t: float
    strike: Optional[float] = None
    option_type: Optional[str] = None


@dataclass(frozen=True)
class VolQuote:
    key: VolKey
    vol: float

    def __post_init__(self) -> None:
        if self.vol < 0.0:
            raise ValueError("vol must be >= 0")


__all__ = ["VolKey", "VolQuote"]
