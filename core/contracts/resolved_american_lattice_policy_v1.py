from __future__ import annotations

from dataclasses import dataclass


AMERICAN_MODEL_FAMILY_ID_V1 = "crr_recombining_binomial_v1"
EARLY_EXERCISE_POLICY_ID_V1 = "strict_gt_continuation_plus_exercise_eps_tie_to_continuation_v1"
CONVERGENCE_POLICY_ID_V1 = "benchmark_only_fixed_step_runtime_v1"
EDGE_CASE_POLICY_ID_V1 = "near_zero_time_intrinsic_zero_vol_deterministic_branch_v1"
BUMP_POLICY_ID_V1 = "numerical_bump_reprice_official_greeks_v1"
TOLERANCE_POLICY_ID_V1 = "numeric_policy_ssot_v1"


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
class ResolvedAmericanLatticePolicyV1:
    """Explicit governed policy surface for Phase D American lattice valuation."""

    model_family_id: str
    step_count: int
    early_exercise_policy_id: str
    convergence_policy_id: str
    edge_case_policy_id: str
    bump_policy_id: str
    tolerance_policy_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "model_family_id",
            _require_exact_policy_id(self.model_family_id, "model_family_id", AMERICAN_MODEL_FAMILY_ID_V1),
        )

        if isinstance(self.step_count, bool) or not isinstance(self.step_count, int) or self.step_count <= 0:
            raise ValueError("step_count must be a positive integer")

        object.__setattr__(
            self,
            "early_exercise_policy_id",
            _require_exact_policy_id(
                self.early_exercise_policy_id,
                "early_exercise_policy_id",
                EARLY_EXERCISE_POLICY_ID_V1,
            ),
        )
        object.__setattr__(
            self,
            "convergence_policy_id",
            _require_exact_policy_id(
                self.convergence_policy_id,
                "convergence_policy_id",
                CONVERGENCE_POLICY_ID_V1,
            ),
        )
        object.__setattr__(
            self,
            "edge_case_policy_id",
            _require_exact_policy_id(self.edge_case_policy_id, "edge_case_policy_id", EDGE_CASE_POLICY_ID_V1),
        )
        object.__setattr__(
            self,
            "bump_policy_id",
            _require_exact_policy_id(self.bump_policy_id, "bump_policy_id", BUMP_POLICY_ID_V1),
        )
        object.__setattr__(
            self,
            "tolerance_policy_id",
            _require_exact_policy_id(self.tolerance_policy_id, "tolerance_policy_id", TOLERANCE_POLICY_ID_V1),
        )


__all__ = [
    "AMERICAN_MODEL_FAMILY_ID_V1",
    "BUMP_POLICY_ID_V1",
    "CONVERGENCE_POLICY_ID_V1",
    "EARLY_EXERCISE_POLICY_ID_V1",
    "EDGE_CASE_POLICY_ID_V1",
    "ResolvedAmericanLatticePolicyV1",
    "TOLERANCE_POLICY_ID_V1",
]