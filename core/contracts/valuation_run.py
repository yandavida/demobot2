from __future__ import annotations

import datetime
from dataclasses import dataclass


def _require_non_empty_string(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")


@dataclass(frozen=True)
class ValuationRun:
    """Canonical lineage parent for deterministic valuation and risk outputs."""

    valuation_run_id: str
    portfolio_state_id: str
    market_snapshot_id: str
    reference_data_set_id: str
    valuation_policy_set_id: str
    valuation_context_id: str
    scenario_set_id: str
    software_build_hash: str
    run_timestamp: datetime.datetime
    valuation_timestamp: datetime.datetime
    run_purpose: str

    def __post_init__(self) -> None:
        for field_name in (
            "valuation_run_id",
            "portfolio_state_id",
            "market_snapshot_id",
            "reference_data_set_id",
            "valuation_policy_set_id",
            "valuation_context_id",
            "scenario_set_id",
            "software_build_hash",
            "run_purpose",
        ):
            _require_non_empty_string(getattr(self, field_name), field_name)

        if not isinstance(self.run_timestamp, datetime.datetime):
            raise ValueError("run_timestamp must be a datetime")
        if self.run_timestamp.tzinfo is None:
            raise ValueError("run_timestamp must be timezone-aware")

        if not isinstance(self.valuation_timestamp, datetime.datetime):
            raise ValueError("valuation_timestamp must be a datetime")
        if self.valuation_timestamp.tzinfo is None:
            raise ValueError("valuation_timestamp must be timezone-aware")


__all__ = ["ValuationRun"]
