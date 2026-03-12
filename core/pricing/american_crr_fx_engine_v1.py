from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from core.contracts.option_valuation_result_v2 import OptionValuationResultV2
from core.contracts.resolved_american_lattice_policy_v1 import ResolvedAmericanLatticePolicyV1
from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedFxOptionValuationInputsV1
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import ThetaRolledFxInputsBoundaryV1
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import theta_rolled_inputs_boundary_reference_v1
from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1
from core.contracts.valuation_measure_result_v2 import ValuationMeasureMethodKindV2
from core.contracts.valuation_measure_result_v2 import ValuationMeasureResultV2
from core.contracts.valuation_measure_set_v1 import PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1
from core.contracts.valuation_measure_set_v1 import PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1
from core.numeric_policy import RHO_1PCT_BUMP_V1
from core.numeric_policy import SPOT_BUMP_RELATIVE_V1
from core.numeric_policy import VEGA_1VOL_ABS_BUMP_V1
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
DELTA_MEASURE_POLICY_ID_V1 = "phase_d.measure_policy.numerical.delta_spot_non_premium_adjusted.v1"
GAMMA_MEASURE_POLICY_ID_V1 = "phase_d.measure_policy.numerical.gamma_spot.v1"
VEGA_MEASURE_POLICY_ID_V1 = "phase_d.measure_policy.numerical.vega_1vol_abs.v1"
THETA_MEASURE_POLICY_ID_V1 = "phase_d.measure_policy.numerical.theta_1d_calendar.v1"
RHO_DOMESTIC_MEASURE_POLICY_ID_V1 = "phase_d.measure_policy.numerical.rho_domestic_1pct.v1"
RHO_FOREIGN_MEASURE_POLICY_ID_V1 = "phase_d.measure_policy.numerical.rho_foreign_1pct.v1"


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


def _present_value_from_inputs_v1(
    resolved_inputs: ResolvedFxOptionValuationInputsV1,
    resolved_lattice_policy: ResolvedAmericanLatticePolicyV1,
) -> Decimal:
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
    return kernel_result.present_value


def _kernel_result_with_overrides_v1(
    resolved_inputs: ResolvedFxOptionValuationInputsV1,
    resolved_lattice_policy: ResolvedAmericanLatticePolicyV1,
    *,
    spot: Decimal | None = None,
    domestic_rate: Decimal | None = None,
    foreign_rate: Decimal | None = None,
    volatility: Decimal | None = None,
) -> CrrAmericanKernelResultV1:
    (
        option_type,
        input_spot,
        strike,
        input_domestic_rate,
        input_foreign_rate,
        input_volatility,
        time_to_expiry_years,
        step_count,
    ) = _extract_kernel_inputs_v1(resolved_inputs, resolved_lattice_policy)

    return crr_american_fx_kernel_v1(
        option_type=option_type,
        spot=input_spot if spot is None else spot,
        strike=strike,
        domestic_rate=input_domestic_rate if domestic_rate is None else domestic_rate,
        foreign_rate=input_foreign_rate if foreign_rate is None else foreign_rate,
        volatility=input_volatility if volatility is None else volatility,
        time_to_expiry_years=time_to_expiry_years,
        step_count=step_count,
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


def _map_full_measures_v1(
    *,
    kernel_result: CrrAmericanKernelResultV1,
    delta: Decimal,
    gamma: Decimal,
    vega: Decimal,
    theta: Decimal,
    rho_domestic: Decimal,
    rho_foreign: Decimal,
    bump_policy_id: str,
    tolerance_policy_id: str,
) -> tuple[ValuationMeasureResultV2, ...]:
    value_by_measure = {
        ValuationMeasureNameV1.PRESENT_VALUE: kernel_result.present_value,
        ValuationMeasureNameV1.INTRINSIC_VALUE: kernel_result.intrinsic_value,
        ValuationMeasureNameV1.TIME_VALUE: kernel_result.time_value,
        ValuationMeasureNameV1.DELTA_SPOT_NON_PREMIUM_ADJUSTED: delta,
        ValuationMeasureNameV1.GAMMA_SPOT: gamma,
        ValuationMeasureNameV1.VEGA_1VOL_ABS: vega,
        ValuationMeasureNameV1.THETA_1D_CALENDAR: theta,
        ValuationMeasureNameV1.RHO_DOMESTIC_1PCT: rho_domestic,
        ValuationMeasureNameV1.RHO_FOREIGN_1PCT: rho_foreign,
    }

    model_direct_policy_id_by_measure = {
        ValuationMeasureNameV1.PRESENT_VALUE: PRESENT_VALUE_MEASURE_POLICY_ID_V1,
        ValuationMeasureNameV1.INTRINSIC_VALUE: INTRINSIC_VALUE_MEASURE_POLICY_ID_V1,
        ValuationMeasureNameV1.TIME_VALUE: TIME_VALUE_MEASURE_POLICY_ID_V1,
    }

    numerical_policy_id_by_measure = {
        ValuationMeasureNameV1.DELTA_SPOT_NON_PREMIUM_ADJUSTED: DELTA_MEASURE_POLICY_ID_V1,
        ValuationMeasureNameV1.GAMMA_SPOT: GAMMA_MEASURE_POLICY_ID_V1,
        ValuationMeasureNameV1.VEGA_1VOL_ABS: VEGA_MEASURE_POLICY_ID_V1,
        ValuationMeasureNameV1.THETA_1D_CALENDAR: THETA_MEASURE_POLICY_ID_V1,
        ValuationMeasureNameV1.RHO_DOMESTIC_1PCT: RHO_DOMESTIC_MEASURE_POLICY_ID_V1,
        ValuationMeasureNameV1.RHO_FOREIGN_1PCT: RHO_FOREIGN_MEASURE_POLICY_ID_V1,
    }

    results: list[ValuationMeasureResultV2] = []
    for measure_name in PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1:
        if measure_name in model_direct_policy_id_by_measure:
            results.append(
                ValuationMeasureResultV2(
                    measure_name=measure_name,
                    value=value_by_measure[measure_name],
                    method_kind=ValuationMeasureMethodKindV2.MODEL_DIRECT,
                    measure_policy_id=model_direct_policy_id_by_measure[measure_name],
                )
            )
        else:
            results.append(
                ValuationMeasureResultV2(
                    measure_name=measure_name,
                    value=value_by_measure[measure_name],
                    method_kind=ValuationMeasureMethodKindV2.NUMERICAL_BUMP_REPRICE,
                    measure_policy_id=numerical_policy_id_by_measure[measure_name],
                    bump_policy_id=bump_policy_id,
                    tolerance_policy_id=tolerance_policy_id,
                )
            )
    return tuple(results)


def _spot_bump_abs_from_spot_v1(spot: Decimal) -> Decimal:
    bump_abs = spot * SPOT_BUMP_RELATIVE_V1
    if bump_abs <= 0:
        raise ValueError("derived spot bump must be > 0")
    if bump_abs >= spot:
        raise ValueError("derived spot bump must be < spot")
    return bump_abs


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

    def value_with_theta_rolled_inputs_boundary(
        self,
        resolved_inputs: ResolvedFxOptionValuationInputsV1,
        resolved_lattice_policy: ResolvedAmericanLatticePolicyV1,
        theta_rolled_inputs_boundary: ThetaRolledFxInputsBoundaryV1,
    ) -> OptionValuationResultV2:
        if not isinstance(theta_rolled_inputs_boundary, ThetaRolledFxInputsBoundaryV1):
            raise ValueError("theta_rolled_inputs_boundary must be ThetaRolledFxInputsBoundaryV1")

        if theta_rolled_inputs_boundary.current_resolved_inputs != resolved_inputs:
            raise ValueError("theta_rolled_inputs_boundary.current_resolved_inputs must equal resolved_inputs")

        model_direct_result = self.value(resolved_inputs, resolved_lattice_policy)

        spot = resolved_inputs.spot.spot
        spot_bump_abs = _spot_bump_abs_from_spot_v1(spot)

        pv_base = model_direct_result.valuation_measures[0].value

        pv_spot_up = _kernel_result_with_overrides_v1(
            resolved_inputs,
            resolved_lattice_policy,
            spot=spot + spot_bump_abs,
        ).present_value
        pv_spot_down = _kernel_result_with_overrides_v1(
            resolved_inputs,
            resolved_lattice_policy,
            spot=spot - spot_bump_abs,
        ).present_value

        delta = (pv_spot_up - pv_spot_down) / (Decimal("2") * spot_bump_abs)
        gamma = (pv_spot_up - (Decimal("2") * pv_base) + pv_spot_down) / (spot_bump_abs * spot_bump_abs)

        pv_vol_up = _kernel_result_with_overrides_v1(
            resolved_inputs,
            resolved_lattice_policy,
            volatility=resolved_inputs.resolved_kernel_scalars.volatility + VEGA_1VOL_ABS_BUMP_V1,
        ).present_value
        vega = pv_vol_up - pv_base

        pv_rd_up = _kernel_result_with_overrides_v1(
            resolved_inputs,
            resolved_lattice_policy,
            domestic_rate=resolved_inputs.resolved_kernel_scalars.domestic_rate + RHO_1PCT_BUMP_V1,
        ).present_value
        rho_domestic = pv_rd_up - pv_base

        pv_rf_up = _kernel_result_with_overrides_v1(
            resolved_inputs,
            resolved_lattice_policy,
            foreign_rate=resolved_inputs.resolved_kernel_scalars.foreign_rate + RHO_1PCT_BUMP_V1,
        ).present_value
        rho_foreign = pv_rf_up - pv_base

        pv_rolled = _present_value_from_inputs_v1(
            theta_rolled_inputs_boundary.theta_rolled_resolved_inputs,
            resolved_lattice_policy,
        )
        theta = pv_rolled - pv_base

        full_measures = _map_full_measures_v1(
            kernel_result=CrrAmericanKernelResultV1(
                present_value=pv_base,
                intrinsic_value=model_direct_result.valuation_measures[1].value,
                time_value=model_direct_result.valuation_measures[2].value,
            ),
            delta=delta,
            gamma=gamma,
            vega=vega,
            theta=theta,
            rho_domestic=rho_domestic,
            rho_foreign=rho_foreign,
            bump_policy_id=resolved_lattice_policy.bump_policy_id,
            tolerance_policy_id=resolved_lattice_policy.tolerance_policy_id,
        )

        return OptionValuationResultV2(
            engine_name=model_direct_result.engine_name,
            engine_version=model_direct_result.engine_version,
            model_name=model_direct_result.model_name,
            model_version=model_direct_result.model_version,
            resolved_input_contract_name=model_direct_result.resolved_input_contract_name,
            resolved_input_contract_version=model_direct_result.resolved_input_contract_version,
            resolved_input_reference=model_direct_result.resolved_input_reference,
            resolved_lattice_policy_contract_name=model_direct_result.resolved_lattice_policy_contract_name,
            resolved_lattice_policy_contract_version=model_direct_result.resolved_lattice_policy_contract_version,
            resolved_lattice_policy_reference=model_direct_result.resolved_lattice_policy_reference,
            theta_roll_boundary_contract_name=THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1,
            theta_roll_boundary_contract_version=THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1,
            theta_roll_boundary_reference=theta_rolled_inputs_boundary_reference_v1(theta_rolled_inputs_boundary),
            valuation_measures=full_measures,
        )


__all__ = [
    "AmericanCrrFxEngineV1",
    "ENGINE_NAME_V1",
    "ENGINE_VERSION_V1",
    "DELTA_MEASURE_POLICY_ID_V1",
    "GAMMA_MEASURE_POLICY_ID_V1",
    "INTRINSIC_VALUE_MEASURE_POLICY_ID_V1",
    "MODEL_NAME_V1",
    "MODEL_VERSION_V1",
    "PRESENT_VALUE_MEASURE_POLICY_ID_V1",
    "RHO_DOMESTIC_MEASURE_POLICY_ID_V1",
    "RHO_FOREIGN_MEASURE_POLICY_ID_V1",
    "RESOLVED_INPUT_CONTRACT_NAME_V1",
    "RESOLVED_INPUT_CONTRACT_VERSION_V1",
    "RESOLVED_LATTICE_POLICY_CONTRACT_NAME_V1",
    "RESOLVED_LATTICE_POLICY_CONTRACT_VERSION_V1",
    "THETA_MEASURE_POLICY_ID_V1",
    "TIME_VALUE_MEASURE_POLICY_ID_V1",
    "VEGA_MEASURE_POLICY_ID_V1",
]
