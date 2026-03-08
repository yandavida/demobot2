from __future__ import annotations

from dataclasses import dataclass

from core.contracts.fx_option_runtime_contract_v1 import FxOptionRuntimeContractV1
from core.contracts.option_runtime_contract_v1 import OptionRuntimeContractV1


def _require_non_empty_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    return value


@dataclass(frozen=True)
class OptionValuationDependencyBundleV1:
    """Canonical dependency bundle for governed option valuation inputs."""

    option_contract: OptionRuntimeContractV1 | FxOptionRuntimeContractV1
    market_snapshot_id: str
    reference_data_set_id: str
    valuation_policy_set_id: str
    valuation_context_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.option_contract, (OptionRuntimeContractV1, FxOptionRuntimeContractV1)):
            raise ValueError(
                "option_contract must be OptionRuntimeContractV1 or FxOptionRuntimeContractV1"
            )

        object.__setattr__(
            self,
            "market_snapshot_id",
            _require_non_empty_string(self.market_snapshot_id, "market_snapshot_id"),
        )
        object.__setattr__(
            self,
            "reference_data_set_id",
            _require_non_empty_string(self.reference_data_set_id, "reference_data_set_id"),
        )
        object.__setattr__(
            self,
            "valuation_policy_set_id",
            _require_non_empty_string(self.valuation_policy_set_id, "valuation_policy_set_id"),
        )
        object.__setattr__(
            self,
            "valuation_context_id",
            _require_non_empty_string(self.valuation_context_id, "valuation_context_id"),
        )


__all__ = ["OptionValuationDependencyBundleV1"]
