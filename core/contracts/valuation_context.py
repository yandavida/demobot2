from __future__ import annotations

import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class ValuationContext:
    valuation_context_id: str
    valuation_timestamp: datetime.datetime
    market_snapshot_id: str
    reference_data_set_id: str
    valuation_policy_set_id: str
    pricing_currency: str
    reporting_currency: str
    run_purpose: str

    def __post_init__(self) -> None:
        for field_name in (
            "valuation_context_id",
            "market_snapshot_id",
            "reference_data_set_id",
            "valuation_policy_set_id",
            "pricing_currency",
            "reporting_currency",
            "run_purpose",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")

        if not isinstance(self.valuation_timestamp, datetime.datetime):
            raise ValueError("valuation_timestamp must be a datetime")
        if self.valuation_timestamp.tzinfo is None:
            raise ValueError("valuation_timestamp must be timezone-aware")

        for ccy_field in ("pricing_currency", "reporting_currency"):
            ccy = getattr(self, ccy_field).strip().upper()
            if len(ccy) != 3:
                raise ValueError(f"{ccy_field} must be a 3-letter currency code")
            object.__setattr__(self, ccy_field, ccy)


__all__ = ["ValuationContext"]
