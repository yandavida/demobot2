from __future__ import annotations

from dataclasses import dataclass

from core.contracts.option_valuation_result_v2 import OptionValuationResultV2
from core.contracts.resolved_american_lattice_policy_v1 import ResolvedAmericanLatticePolicyV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedFxOptionValuationInputsV1
from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1
from core.contracts.valuation_measure_result_v2 import ValuationMeasureMethodKindV2
from core.contracts.valuation_measure_result_v2 import ValuationMeasureResultV2
from core.contracts.valuation_measure_set_v1 import PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1
from core.pricing.crr_american_fx_kernel_v1 import CrrAmericanKernelResultV1
from core.pricing.crr_american_fx_kernel_v1 import crr_american_fx_kernel_v1


ENGINE_NAME_V1 = "american_crr_fx_engine"
ENGINE_VERSION_V1 = "1.0.0"
MODEL_NAME_V1 = "crr_recombining_binomial"
MODEL_VERSION_V1 = "1.0.0"
RESOLVED_INPUT_CONTRACT_NAME_V1 = "ResolvedFxOptionValuationInputsV1"
RESOLVED_INPUT_CONTRACT_VERSION_V1 = "1.0.0"
RESOLVED_LATTICE_POLICY_CONTRACT_NAME_V1 = "ResolvedAmericanLatticePolicyV1"
RESOLVED_LATTICE_POLICY_CONTRACT_VERSION_V1 = "1.0.0"

PRESENT_VALUE_MEASURE_POLICY_ID_V1 = "phase_d.measure_policy.model_direct.present_value.v1"
INTRINSIC_VALUE_MEASURE_POLICY_ID_V1 = "phase_d.measure_policy.model_direct.intrinsic_value.v1"
TIME_VALUE_MEASURE_POLICY_ID_V1 = "phase_d.measure_policy.model_direct.time_value.v1"


def _require_non_empty_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    return value


def _extract_kernel_inputs_v1(
    resolved_inputs: ResolvedFxOptionValuationInputsV1,
    resolved_lattice_policy: ResolvedAmericanLatticePolicyV1,
) -> tuple:
    if resolved_inputs.fx_option_contract.exercise_style != "american":
        raise ValueError("fx_option_contract.exercise_style must be american for AmericanCrrFxEngineV1")

    scalars = resolved_inputs.resolved_kernel_scalars
    return (
        resolved_inputs.fx_option_contract.option_type,
        resolved_inputs.spot.spot,
        resolved_inputs.fx_option_contract.strike,
        scalars.domestic_rate,
        scalars.foreign_rate,
        scalars.volatility,
        scalars.time_to_expiry_years,
        resolved_lattice_policy.step_count,
    )


def _resolved_lattice_policy_reference_v1(policy: ResolvedAmericanLatticePolicyV1) -> str:
    return (
        "ResolvedAmericanLatticePolicyV1:"
        f"model_family_id={policy.model_family_id};"
        f"step_count={policy.step_count};"
        f"early_exercise_policy_id={policy.early_exercise_policy_id};"
        f"convergence_policy_id={policy.convergence_policy_id};"
        f"edge_case_policy_id={policy.edge_case_policy_id};"
        f"bump_policy_id={policy.bump_policy_id};"
        f"tolerance_policy_id={policy.tolerance_policy_id}"
    )


def _map_model_direct_measures_v1(kernel_result: CrrAmericanKernelResultV1) -> tuple[ValuationMeasureResultV2, ...]:
    value_by_measure = {
        ValuationMeasureNameV1.PRESENT_VALUE: kernel_result.present_value,
        ValuationMeasureNameV1.INTRINSIC_VALUE: kernel_result.intrinsic_value,
        ValuationMeasureNameV1.TIME_VALUE: kernel_result.time_value,
    }
    policy_id_by_measure = {
        ValuationMeasureNameV1.PRESENT_VALUE: PRESENT_VALUE_MEASURE_POLICY_ID_V1,
        ValuationMeasureNameV1.INTRINSIC_VALUE: INTRINSIC_VALUE_MEASURE_POLICY_ID_V1,
        ValuationMeasureNameV1.TIME_VALUE: TIME_VALUE_MEASURE_POLICY_ID_V1,
    }

    return tuple(
        ValuationMeasureResultV2(
            measure_name=measure_name,
            value=value_by_measure[measure_name],
            method_kind=ValuationMeasureMethodKindV2.MODEL_DIRECT,
            measure_policy_id=policy_id_by_measure[measure_name],
        )
        for measure_name in PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1
    )


@dataclass(frozen=True)
class AmericanCrrFxEngineV1:
    """Narrow governed PR-D1.4 wrapper from resolved inputs and lattice policy to OptionValuationResultV2."""

    engine_name: str = ENGINE_NAME_V1
    engine_version: str = ENGINE_VERSION_V1
    model_name: str = MODEL_NAME_V1
    model_version: str = MODEL_VERSION_V1

    def value(
        self,
        resolved_inputs: ResolvedFxOptionValuationInputsV1,
        resolved_lattice_policy: ResolvedAmericanLatticePolicyV1,
    ) -> OptionValuationResultV2:
        if not isinstance(resolved_inputs, ResolvedFxOptionValuationInputsV1):
            raise ValueError("AmericanCrrFxEngineV1 requires ResolvedFxOptionValuationInputsV1")
        if not isinstance(resolved_lattice_policy, ResolvedAmericanLatticePolicyV1):
            raise ValueError("AmericanCrrFxEngineV1 requires ResolvedAmericanLatticePolicyV1")

        _require_non_empty_string(resolved_inputs.resolved_basis_hash, "resolved_basis_hash")

        (
            option_type,
            spot,
            strike,
            domestic_rate,
            foreign_rate,
            volatility,
            time_to_expiry_years,
            step_count,
        ) = _extract_kernel_inputs_v1(resolved_inputs, resolved_lattice_policy)

        kernel_result = crr_american_fx_kernel_v1(
            option_type=option_type,
            spot=spot,
            strike=strike,
            domestic_rate=domestic_rate,
            foreign_rate=foreign_rate,
            volatility=volatility,
            time_to_expiry_years=time_to_expiry_years,
            step_count=step_count,
        )

        return OptionValuationResultV2(
            engine_name=_require_non_empty_string(self.engine_name, "engine_name"),
            engine_version=_require_non_empty_string(self.engine_version, "engine_version"),
            model_name=_require_non_empty_string(self.model_name, "model_name"),
            model_version=_require_non_empty_string(self.model_version, "model_version"),
            resolved_input_contract_name=RESOLVED_INPUT_CONTRACT_NAME_V1,
            resolved_input_contract_version=RESOLVED_INPUT_CONTRACT_VERSION_V1,
            resolved_input_reference=resolved_inputs.resolved_basis_hash,
            resolved_lattice_policy_contract_name=RESOLVED_LATTICE_POLICY_CONTRACT_NAME_V1,
            resolved_lattice_policy_contract_version=RESOLVED_LATTICE_POLICY_CONTRACT_VERSION_V1,
            resolved_lattice_policy_reference=_resolved_lattice_policy_reference_v1(resolved_lattice_policy),
            valuation_measures=_map_model_direct_measures_v1(kernel_result),
        )


__all__ = [
    "AmericanCrrFxEngineV1",
    "ENGINE_NAME_V1",
    "ENGINE_VERSION_V1",
    "INTRINSIC_VALUE_MEASURE_POLICY_ID_V1",
    "MODEL_NAME_V1",
    "MODEL_VERSION_V1",
    "PRESENT_VALUE_MEASURE_POLICY_ID_V1",
    "RESOLVED_INPUT_CONTRACT_NAME_V1",
    "RESOLVED_INPUT_CONTRACT_VERSION_V1",
    "RESOLVED_LATTICE_POLICY_CONTRACT_NAME_V1",
    "RESOLVED_LATTICE_POLICY_CONTRACT_VERSION_V1",
    "TIME_VALUE_MEASURE_POLICY_ID_V1",
]
