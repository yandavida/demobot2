from __future__ import annotations

from dataclasses import dataclass
import datetime


@dataclass(frozen=True, slots=True)
class ValuationContext:
    as_of_ts: datetime.datetime
    domestic_currency: str
    strict_mode: bool = True

    def __post_init__(self):
        if self.as_of_ts.tzinfo is None:
            raise ValueError("as_of_ts must be timezone-aware")

        if self.domestic_currency.strip() == "":
            raise ValueError("domestic_currency must be non-empty")
