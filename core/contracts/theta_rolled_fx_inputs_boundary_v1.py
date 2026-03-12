from __future__ import annotations

from dataclasses import dataclass

from core.contracts.resolved_option_valuation_inputs_v1 import ResolvedFxOptionValuationInputsV1


THETA_ROLLED_INPUT_POLICY_ID_V1 = "theta_rolled_resolved_input_1d_calendar_upstream_v1"
THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1 = "ThetaRolledFxInputsBoundaryV1"
THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1 = "1.0.0"


def _require_non_empty_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    return value


def _require_exact_policy_id(value: str, field_name: str, expected: str) -> str:
    normalized = _require_non_empty_string(value, field_name)
    if normalized != expected:
        raise ValueError(f"{field_name} must equal {expected}")
    return normalized


@dataclass(frozen=True)
class ThetaRolledFxInputsBoundaryV1:
    """Governed boundary for upstream-prepared theta rolled-input repricing."""

    current_resolved_inputs: ResolvedFxOptionValuationInputsV1
    theta_rolled_resolved_inputs: ResolvedFxOptionValuationInputsV1
    theta_roll_policy_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.current_resolved_inputs, ResolvedFxOptionValuationInputsV1):
            raise ValueError("current_resolved_inputs must be ResolvedFxOptionValuationInputsV1")
        if not isinstance(self.theta_rolled_resolved_inputs, ResolvedFxOptionValuationInputsV1):
            raise ValueError("theta_rolled_resolved_inputs must be ResolvedFxOptionValuationInputsV1")

        if self.current_resolved_inputs is self.theta_rolled_resolved_inputs:
            raise ValueError("current_resolved_inputs and theta_rolled_resolved_inputs must be explicitly distinct")

        if self.current_resolved_inputs.fx_option_contract != self.theta_rolled_resolved_inputs.fx_option_contract:
            raise ValueError(
                "current_resolved_inputs and theta_rolled_resolved_inputs must reference the same fx_option_contract"
            )

        current_time_to_expiry = self.current_resolved_inputs.resolved_kernel_scalars.time_to_expiry_years
        rolled_time_to_expiry = self.theta_rolled_resolved_inputs.resolved_kernel_scalars.time_to_expiry_years
        if rolled_time_to_expiry > current_time_to_expiry:
            raise ValueError(
                "theta_rolled_resolved_inputs.resolved_kernel_scalars.time_to_expiry_years "
                "must be <= current_resolved_inputs.resolved_kernel_scalars.time_to_expiry_years"
            )

        object.__setattr__(
            self,
            "theta_roll_policy_id",
            _require_exact_policy_id(
                self.theta_roll_policy_id,
                "theta_roll_policy_id",
                THETA_ROLLED_INPUT_POLICY_ID_V1,
            ),
        )


def theta_rolled_inputs_boundary_reference_v1(boundary: ThetaRolledFxInputsBoundaryV1) -> str:
    if not isinstance(boundary, ThetaRolledFxInputsBoundaryV1):
        raise ValueError("boundary must be ThetaRolledFxInputsBoundaryV1")

    return (
        f"{THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1}:"
        f"current_resolved_input_reference={boundary.current_resolved_inputs.resolved_basis_hash};"
        f"theta_rolled_resolved_input_reference={boundary.theta_rolled_resolved_inputs.resolved_basis_hash};"
        f"theta_roll_policy_id={boundary.theta_roll_policy_id}"
    )


__all__ = [
    "THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1",
    "THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1",
    "THETA_ROLLED_INPUT_POLICY_ID_V1",
    "ThetaRolledFxInputsBoundaryV1",
    "theta_rolled_inputs_boundary_reference_v1",
]
