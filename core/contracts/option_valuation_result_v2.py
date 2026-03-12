from __future__ import annotations

from dataclasses import dataclass

from core.contracts.theta_rolled_fx_inputs_boundary_v1 import THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1
from core.contracts.valuation_measure_result_v2 import ValuationMeasureResultV2
from core.contracts.valuation_measure_set_v1 import PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1
from core.contracts.valuation_measure_set_v1 import PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1


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
    theta_roll_boundary_contract_name: str | None = None
    theta_roll_boundary_contract_version: str | None = None
    theta_roll_boundary_reference: str | None = None

    _ALLOWED_MEASURE_ORDERS_V1: tuple[tuple, ...] = (
        PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1,
        PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1,
    )

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

        theta_lineage_values = (
            self.theta_roll_boundary_contract_name,
            self.theta_roll_boundary_contract_version,
            self.theta_roll_boundary_reference,
        )
        populated_theta_lineage_count = sum(value is not None for value in theta_lineage_values)
        if populated_theta_lineage_count not in {0, 3}:
            raise ValueError(
                "theta boundary lineage fields must be all populated or all None"
            )

        if self.theta_roll_boundary_contract_name is not None:
            object.__setattr__(
                self,
                "theta_roll_boundary_contract_name",
                _require_non_empty_string(self.theta_roll_boundary_contract_name, "theta_roll_boundary_contract_name"),
            )
            if self.theta_roll_boundary_contract_name != THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1:
                raise ValueError(
                    "theta_roll_boundary_contract_name must equal "
                    f"{THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1}"
                )
        if self.theta_roll_boundary_contract_version is not None:
            object.__setattr__(
                self,
                "theta_roll_boundary_contract_version",
                _require_non_empty_string(
                    self.theta_roll_boundary_contract_version,
                    "theta_roll_boundary_contract_version",
                ),
            )
            if self.theta_roll_boundary_contract_version != THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1:
                raise ValueError(
                    "theta_roll_boundary_contract_version must equal "
                    f"{THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1}"
                )
        if self.theta_roll_boundary_reference is not None:
            object.__setattr__(
                self,
                "theta_roll_boundary_reference",
                _require_non_empty_string(self.theta_roll_boundary_reference, "theta_roll_boundary_reference"),
            )

        if not isinstance(self.valuation_measures, tuple):
            raise ValueError("valuation_measures must be a tuple")
        if len(self.valuation_measures) not in {
            len(PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1),
            len(PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1),
        }:
            raise ValueError("valuation_measures must match an approved governed measure set")

        for measure in self.valuation_measures:
            if not isinstance(measure, ValuationMeasureResultV2):
                raise ValueError("valuation_measures entries must be ValuationMeasureResultV2")

        provided_order = tuple(measure.measure_name for measure in self.valuation_measures)
        if provided_order not in self._ALLOWED_MEASURE_ORDERS_V1:
            raise ValueError("valuation_measures must match an approved governed canonical order")

        if provided_order == PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1 and populated_theta_lineage_count != 0:
            raise ValueError(
                "theta boundary lineage must be None for model-direct measure set"
            )

        if provided_order == PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1:
            if self.theta_roll_boundary_contract_name is None:
                raise ValueError(
                    "theta_roll_boundary_contract_name is required for full canonical measure set"
                )
            if self.theta_roll_boundary_contract_version is None:
                raise ValueError(
                    "theta_roll_boundary_contract_version is required for full canonical measure set"
                )
            if self.theta_roll_boundary_reference is None:
                raise ValueError(
                    "theta_roll_boundary_reference is required for full canonical measure set"
                )


__all__ = ["OptionValuationResultV2"]