from __future__ import annotations

from dataclasses import FrozenInstanceError
from dataclasses import fields

import pytest

from core.contracts.resolved_american_lattice_policy_v1 import AMERICAN_MODEL_FAMILY_ID_V1
from core.contracts.resolved_american_lattice_policy_v1 import BUMP_POLICY_ID_V1
from core.contracts.resolved_american_lattice_policy_v1 import CONVERGENCE_POLICY_ID_V1
from core.contracts.resolved_american_lattice_policy_v1 import EARLY_EXERCISE_POLICY_ID_V1
from core.contracts.resolved_american_lattice_policy_v1 import EDGE_CASE_POLICY_ID_V1
from core.contracts.resolved_american_lattice_policy_v1 import ResolvedAmericanLatticePolicyV1
from core.contracts.resolved_american_lattice_policy_v1 import TOLERANCE_POLICY_ID_V1


def _policy(*, step_count: int = 200) -> ResolvedAmericanLatticePolicyV1:
    return ResolvedAmericanLatticePolicyV1(
        model_family_id=AMERICAN_MODEL_FAMILY_ID_V1,
        step_count=step_count,
        early_exercise_policy_id=EARLY_EXERCISE_POLICY_ID_V1,
        convergence_policy_id=CONVERGENCE_POLICY_ID_V1,
        edge_case_policy_id=EDGE_CASE_POLICY_ID_V1,
        bump_policy_id=BUMP_POLICY_ID_V1,
        tolerance_policy_id=TOLERANCE_POLICY_ID_V1,
    )


def test_contract_has_explicit_governed_policy_fields() -> None:
    field_names = tuple(field.name for field in fields(ResolvedAmericanLatticePolicyV1))

    assert field_names == (
        "model_family_id",
        "step_count",
        "early_exercise_policy_id",
        "convergence_policy_id",
        "edge_case_policy_id",
        "bump_policy_id",
        "tolerance_policy_id",
    )


def test_contract_is_immutable() -> None:
    policy = _policy()

    with pytest.raises(FrozenInstanceError):
        policy.step_count = 100  # type: ignore[misc]


def test_crr_only_model_family_is_enforced() -> None:
    with pytest.raises(ValueError, match="model_family_id"):
        ResolvedAmericanLatticePolicyV1(
            model_family_id="jarrow_rudd_v1",
            step_count=200,
            early_exercise_policy_id=EARLY_EXERCISE_POLICY_ID_V1,
            convergence_policy_id=CONVERGENCE_POLICY_ID_V1,
            edge_case_policy_id=EDGE_CASE_POLICY_ID_V1,
            bump_policy_id=BUMP_POLICY_ID_V1,
            tolerance_policy_id=TOLERANCE_POLICY_ID_V1,
        )


def test_step_count_is_explicit_positive_integer() -> None:
    with pytest.raises(ValueError, match="step_count"):
        _policy(step_count=0)

    with pytest.raises(ValueError, match="step_count"):
        _policy(step_count=-1)

    with pytest.raises(ValueError, match="step_count"):
        ResolvedAmericanLatticePolicyV1(
            model_family_id=AMERICAN_MODEL_FAMILY_ID_V1,
            step_count="200",  # type: ignore[arg-type]
            early_exercise_policy_id=EARLY_EXERCISE_POLICY_ID_V1,
            convergence_policy_id=CONVERGENCE_POLICY_ID_V1,
            edge_case_policy_id=EDGE_CASE_POLICY_ID_V1,
            bump_policy_id=BUMP_POLICY_ID_V1,
            tolerance_policy_id=TOLERANCE_POLICY_ID_V1,
        )


def test_rejects_ungoverned_policy_identity_values() -> None:
    with pytest.raises(ValueError, match="early_exercise_policy_id"):
        ResolvedAmericanLatticePolicyV1(
            model_family_id=AMERICAN_MODEL_FAMILY_ID_V1,
            step_count=200,
            early_exercise_policy_id="exercise_on_equality_v1",
            convergence_policy_id=CONVERGENCE_POLICY_ID_V1,
            edge_case_policy_id=EDGE_CASE_POLICY_ID_V1,
            bump_policy_id=BUMP_POLICY_ID_V1,
            tolerance_policy_id=TOLERANCE_POLICY_ID_V1,
        )


def test_no_economic_state_leakage_or_speculative_semantics_in_contract_shape() -> None:
    forbidden = {
        "spot",
        "strike",
        "volatility",
        "domestic_rate",
        "foreign_rate",
        "market",
        "portfolio",
        "scenario",
        "basket",
        "lifecycle",
        "advisory",
    }

    field_names = {field.name for field in fields(ResolvedAmericanLatticePolicyV1)}
    assert field_names.isdisjoint(forbidden)


def test_identity_constants_are_stable_and_non_empty() -> None:
    assert AMERICAN_MODEL_FAMILY_ID_V1 == "crr_recombining_binomial_v1"
    assert EARLY_EXERCISE_POLICY_ID_V1 == "strict_gt_continuation_plus_exercise_eps_tie_to_continuation_v1"
    assert CONVERGENCE_POLICY_ID_V1 == "benchmark_only_fixed_step_runtime_v1"
    assert EDGE_CASE_POLICY_ID_V1 == "near_zero_time_intrinsic_zero_vol_deterministic_branch_v1"
    assert BUMP_POLICY_ID_V1 == "numerical_bump_reprice_official_greeks_v1"
    assert TOLERANCE_POLICY_ID_V1 == "numeric_policy_ssot_v1"

    for value in (
        AMERICAN_MODEL_FAMILY_ID_V1,
        EARLY_EXERCISE_POLICY_ID_V1,
        CONVERGENCE_POLICY_ID_V1,
        EDGE_CASE_POLICY_ID_V1,
        BUMP_POLICY_ID_V1,
        TOLERANCE_POLICY_ID_V1,
    ):
        assert isinstance(value, str)
        assert value