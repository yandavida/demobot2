from __future__ import annotations

from dataclasses import dataclass

from core.contracts.valuation_measure_result_v2 import ValuationMeasureResultV2
from core.contracts.valuation_measure_set_v1 import PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1


def _require_non_empty_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    return value


@dataclass(frozen=True)
class OptionValuationResultV2:
    """Immutable governed valuation result contract for single-trade Phase D option valuation."""

    engine_name: str
    engine_version: str
    model_name: str
    model_version: str
    resolved_input_contract_name: str
    resolved_input_contract_version: str
    resolved_input_reference: str
    resolved_lattice_policy_contract_name: str
    resolved_lattice_policy_contract_version: str
    resolved_lattice_policy_reference: str
    valuation_measures: tuple[ValuationMeasureResultV2, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "engine_name", _require_non_empty_string(self.engine_name, "engine_name"))
        object.__setattr__(self, "engine_version", _require_non_empty_string(self.engine_version, "engine_version"))
        object.__setattr__(self, "model_name", _require_non_empty_string(self.model_name, "model_name"))
        object.__setattr__(self, "model_version", _require_non_empty_string(self.model_version, "model_version"))
        object.__setattr__(
            self,
            "resolved_input_contract_name",
            _require_non_empty_string(self.resolved_input_contract_name, "resolved_input_contract_name"),
        )
        object.__setattr__(
            self,
            "resolved_input_contract_version",
            _require_non_empty_string(self.resolved_input_contract_version, "resolved_input_contract_version"),
        )
        object.__setattr__(
            self,
            "resolved_input_reference",
            _require_non_empty_string(self.resolved_input_reference, "resolved_input_reference"),
        )
        object.__setattr__(
            self,
            "resolved_lattice_policy_contract_name",
            _require_non_empty_string(
                self.resolved_lattice_policy_contract_name,
                "resolved_lattice_policy_contract_name",
            ),
        )
        object.__setattr__(
            self,
            "resolved_lattice_policy_contract_version",
            _require_non_empty_string(
                self.resolved_lattice_policy_contract_version,
                "resolved_lattice_policy_contract_version",
            ),
        )
        object.__setattr__(
            self,
            "resolved_lattice_policy_reference",
            _require_non_empty_string(
                self.resolved_lattice_policy_reference,
                "resolved_lattice_policy_reference",
            ),
        )

        if not isinstance(self.valuation_measures, tuple):
            raise ValueError("valuation_measures must be a tuple")
        if len(self.valuation_measures) != len(PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1):
            raise ValueError("valuation_measures must contain exactly the approved Phase measure set")

        for measure in self.valuation_measures:
            if not isinstance(measure, ValuationMeasureResultV2):
                raise ValueError("valuation_measures entries must be ValuationMeasureResultV2")

        provided_order = tuple(measure.measure_name for measure in self.valuation_measures)
        if provided_order != PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1:
            raise ValueError("valuation_measures must match approved measures in canonical order")


__all__ = ["OptionValuationResultV2"]