from __future__ import annotations

from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedFxOptionValuationInputsV1
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import THETA_ROLLED_INPUT_POLICY_ID_V1
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import ThetaRolledFxInputsBoundaryV1


def _require_non_empty_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    return value


def prepare_theta_rolled_fx_inputs_boundary_v1(
    *,
    current_resolved_inputs: ResolvedFxOptionValuationInputsV1,
    theta_rolled_resolved_inputs: ResolvedFxOptionValuationInputsV1,
) -> ThetaRolledFxInputsBoundaryV1:
    """Prepare governed theta rolled-input boundary from two upstream-prepared resolved inputs."""

    if not isinstance(current_resolved_inputs, ResolvedFxOptionValuationInputsV1):
        raise ValueError("current_resolved_inputs must be ResolvedFxOptionValuationInputsV1")
    if not isinstance(theta_rolled_resolved_inputs, ResolvedFxOptionValuationInputsV1):
        raise ValueError("theta_rolled_resolved_inputs must be ResolvedFxOptionValuationInputsV1")

    if current_resolved_inputs is theta_rolled_resolved_inputs:
        raise ValueError("current_resolved_inputs and theta_rolled_resolved_inputs must be distinct objects")

    if current_resolved_inputs.fx_option_contract != theta_rolled_resolved_inputs.fx_option_contract:
        raise ValueError("current_resolved_inputs and theta_rolled_resolved_inputs must reference the same fx_option_contract")

    current_basis_hash = _require_non_empty_string(
        current_resolved_inputs.resolved_basis_hash,
        "current_resolved_inputs.resolved_basis_hash",
    )
    rolled_basis_hash = _require_non_empty_string(
        theta_rolled_resolved_inputs.resolved_basis_hash,
        "theta_rolled_resolved_inputs.resolved_basis_hash",
    )

    if current_basis_hash == rolled_basis_hash:
        raise ValueError("resolved_basis_hash must differ between current_resolved_inputs and theta_rolled_resolved_inputs")

    current_time_to_expiry = current_resolved_inputs.resolved_kernel_scalars.time_to_expiry_years
    rolled_time_to_expiry = theta_rolled_resolved_inputs.resolved_kernel_scalars.time_to_expiry_years
    if not rolled_time_to_expiry < current_time_to_expiry:
        raise ValueError(
            "theta_rolled_resolved_inputs.resolved_kernel_scalars.time_to_expiry_years "
            "must be strictly less than current_resolved_inputs.resolved_kernel_scalars.time_to_expiry_years"
        )

    return ThetaRolledFxInputsBoundaryV1(
        current_resolved_inputs=current_resolved_inputs,
        theta_rolled_resolved_inputs=theta_rolled_resolved_inputs,
        theta_roll_policy_id=THETA_ROLLED_INPUT_POLICY_ID_V1,
    )


__all__ = ["prepare_theta_rolled_fx_inputs_boundary_v1"]
