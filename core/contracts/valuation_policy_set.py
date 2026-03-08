from __future__ import annotations

import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class ValuationPolicySet:
    valuation_policy_id: str
    model_family: str
    pricing_engine_policy: str
    numeric_policy_id: str
    tolerance_policy_id: str
    calibration_recipe_id: str
    approval_status: str
    policy_version: str
    policy_owner: str
    created_timestamp: datetime.datetime

    def __post_init__(self) -> None:
        for field_name in (
            "valuation_policy_id",
            "model_family",
            "pricing_engine_policy",
            "numeric_policy_id",
            "tolerance_policy_id",
            "calibration_recipe_id",
            "approval_status",
            "policy_version",
            "policy_owner",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")

        if not isinstance(self.created_timestamp, datetime.datetime):
            raise ValueError("created_timestamp must be a datetime")
        if self.created_timestamp.tzinfo is None:
            raise ValueError("created_timestamp must be timezone-aware")


__all__ = ["ValuationPolicySet"]
