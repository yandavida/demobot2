from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1


class ValuationMeasureMethodKindV2(str, Enum):
    """Governed method kind for single-trade valuation measure provenance."""

    ANALYTICAL = "analytical"
    NUMERICAL_BUMP_REPRICE = "numerical_bump_reprice"


def _require_non_empty_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    return value


@dataclass(frozen=True)
class ValuationMeasureResultV2:
    """Immutable governed single-trade valuation measure result with explicit provenance."""

    measure_name: ValuationMeasureNameV1
    value: Decimal
    method_kind: ValuationMeasureMethodKindV2
    measure_policy_id: str
    bump_policy_id: str | None = None
    tolerance_policy_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.measure_name, ValuationMeasureNameV1):
            raise ValueError("measure_name must be ValuationMeasureNameV1")
        if not isinstance(self.value, Decimal):
            raise ValueError("value must be Decimal")
        if not self.value.is_finite():
            raise ValueError("value must be finite")
        if not isinstance(self.method_kind, ValuationMeasureMethodKindV2):
            raise ValueError("method_kind must be ValuationMeasureMethodKindV2")

        object.__setattr__(
            self,
            "measure_policy_id",
            _require_non_empty_string(self.measure_policy_id, "measure_policy_id"),
        )

        if self.bump_policy_id is not None:
            object.__setattr__(
                self,
                "bump_policy_id",
                _require_non_empty_string(self.bump_policy_id, "bump_policy_id"),
            )
        if self.tolerance_policy_id is not None:
            object.__setattr__(
                self,
                "tolerance_policy_id",
                _require_non_empty_string(self.tolerance_policy_id, "tolerance_policy_id"),
            )

        if self.method_kind == ValuationMeasureMethodKindV2.NUMERICAL_BUMP_REPRICE:
            if self.bump_policy_id is None:
                raise ValueError("bump_policy_id is required when method_kind is numerical_bump_reprice")
            if self.tolerance_policy_id is None:
                raise ValueError("tolerance_policy_id is required when method_kind is numerical_bump_reprice")


__all__ = [
    "ValuationMeasureMethodKindV2",
    "ValuationMeasureResultV2",
]