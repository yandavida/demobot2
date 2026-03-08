from __future__ import annotations

import datetime

import pytest

from core.contracts.model_registry import ModelCapability
from core.contracts.model_registry import ModelRegistryEntry
from core.validation.validation_scaffold_v1 import ArtifactSchemaRefV1
from core.validation.validation_scaffold_v1 import BenchmarkCaseV1
from core.validation.validation_scaffold_v1 import check_engine_approval_metadata_v1
from core.validation.validation_scaffold_v1 import check_replay_determinism_v1
from core.validation.validation_scaffold_v1 import ensure_expected_artifact_schema_v1
from core.validation.validation_scaffold_v1 import parse_artifact_schema_ref_v1
from core.validation.validation_scaffold_v1 import ReplayCaseV1
from core.validation.validation_scaffold_v1 import run_benchmark_case_v1


def _approved_model_entry() -> ModelRegistryEntry:
    return ModelRegistryEntry(
        model_id="model.fx.bs.v1",
        semantic_version="1.0.0",
        implementation_version="impl-2026-03-08",
        validation_status="approved",
        owner="treasury_model_risk",
        approval_date=datetime.date(2026, 3, 8),
        benchmark_pack_id="bench.fx.options.v1",
        known_limitations=("european-only",),
        numeric_policy_id="numeric.policy.v1",
        supported_capabilities=(
            ModelCapability(
                instrument_family="fx_option_vanilla",
                exercise_style="european",
                measure="pv",
            ),
        ),
    )


def test_artifact_schema_ref_requires_explicit_fields() -> None:
    with pytest.raises(ValueError, match="schema_version"):
        parse_artifact_schema_ref_v1({"schema_name": "pe.artifact"})


def test_artifact_schema_expected_version_check_is_explicit() -> None:
    schema_ref = ArtifactSchemaRefV1(schema_name="pe.advisory_payload", schema_version="1.0")

    ensure_expected_artifact_schema_v1(
        schema_ref,
        expected_schema_name="pe.advisory_payload",
        expected_schema_version="1.0",
    )

    with pytest.raises(ValueError, match="schema_version"):
        ensure_expected_artifact_schema_v1(
            schema_ref,
            expected_schema_name="pe.advisory_payload",
            expected_schema_version="2.0",
        )


def test_benchmark_harness_skeleton_is_structurally_deterministic() -> None:
    case = BenchmarkCaseV1(
        case_id="bench-case-001",
        model_id="model.fx.bs.v1",
        benchmark_pack_id="bench.fx.options.v1",
        valuation_run_id="vr-2026-03-08-001",
    )

    result_1 = run_benchmark_case_v1(
        case,
        expected_hash="sha256:aaa",
        observed_hash="sha256:aaa",
    )
    result_2 = run_benchmark_case_v1(
        case,
        expected_hash="sha256:aaa",
        observed_hash="sha256:aaa",
    )

    assert result_1 == result_2
    assert result_1.is_match is True


def test_replay_scaffold_is_structurally_deterministic() -> None:
    case = ReplayCaseV1(
        replay_id="replay-001",
        valuation_run_id="vr-2026-03-08-001",
        artifact_id="artifact-001",
    )

    result_1 = check_replay_determinism_v1(
        case,
        first_hash="sha256:bbb",
        second_hash="sha256:bbb",
    )
    result_2 = check_replay_determinism_v1(
        case,
        first_hash="sha256:bbb",
        second_hash="sha256:bbb",
    )

    assert result_1 == result_2
    assert result_1.is_deterministic is True


def test_engine_approval_metadata_check_accepts_approved_shape() -> None:
    result = check_engine_approval_metadata_v1(_approved_model_entry())

    assert result.is_approved is True
    assert result.issues == ()


def test_engine_approval_metadata_check_rejects_non_approved_status() -> None:
    provisional = ModelRegistryEntry(
        model_id="model.fx.bs.v1",
        semantic_version="1.0.0",
        implementation_version="impl-2026-03-08",
        validation_status="provisional",
        owner="treasury_model_risk",
        approval_date=datetime.date(2026, 3, 8),
        benchmark_pack_id="bench.fx.options.v1",
        known_limitations=("european-only",),
        numeric_policy_id="numeric.policy.v1",
        supported_capabilities=(
            ModelCapability(
                instrument_family="fx_option_vanilla",
                exercise_style="european",
                measure="pv",
            ),
        ),
    )

    result = check_engine_approval_metadata_v1(provisional)

    assert result.is_approved is False
    assert "validation_status_not_approved" in result.issues


def _unchecked_model_entry(*, benchmark_pack_id: str, numeric_policy_id: str, supported_capabilities: tuple[ModelCapability, ...]) -> ModelRegistryEntry:
    """Create a ModelRegistryEntry shape without running dataclass invariants.

    This isolates validation_scaffold_v1 negative-path behavior for governance fields.
    """

    entry = object.__new__(ModelRegistryEntry)
    object.__setattr__(entry, "model_id", "model.fx.bs.v1")
    object.__setattr__(entry, "semantic_version", "1.0.0")
    object.__setattr__(entry, "implementation_version", "impl-2026-03-08")
    object.__setattr__(entry, "validation_status", "approved")
    object.__setattr__(entry, "owner", "treasury_model_risk")
    object.__setattr__(entry, "approval_date", datetime.date(2026, 3, 8))
    object.__setattr__(entry, "benchmark_pack_id", benchmark_pack_id)
    object.__setattr__(entry, "known_limitations", ("european-only",))
    object.__setattr__(entry, "numeric_policy_id", numeric_policy_id)
    object.__setattr__(entry, "supported_capabilities", supported_capabilities)
    return entry


def test_engine_approval_metadata_check_rejects_missing_benchmark_pack_id() -> None:
    entry = _unchecked_model_entry(
        benchmark_pack_id="",
        numeric_policy_id="numeric.policy.v1",
        supported_capabilities=(
            ModelCapability(
                instrument_family="fx_option_vanilla",
                exercise_style="european",
                measure="pv",
            ),
        ),
    )

    result = check_engine_approval_metadata_v1(entry)

    assert result.is_approved is False
    assert "missing_benchmark_pack_id" in result.issues


def test_engine_approval_metadata_check_rejects_missing_numeric_policy_id() -> None:
    entry = _unchecked_model_entry(
        benchmark_pack_id="bench.fx.options.v1",
        numeric_policy_id="",
        supported_capabilities=(
            ModelCapability(
                instrument_family="fx_option_vanilla",
                exercise_style="european",
                measure="pv",
            ),
        ),
    )

    result = check_engine_approval_metadata_v1(entry)

    assert result.is_approved is False
    assert "missing_numeric_policy_id" in result.issues


def test_engine_approval_metadata_check_rejects_missing_supported_capabilities() -> None:
    entry = _unchecked_model_entry(
        benchmark_pack_id="bench.fx.options.v1",
        numeric_policy_id="numeric.policy.v1",
        supported_capabilities=(),
    )

    result = check_engine_approval_metadata_v1(entry)

    assert result.is_approved is False
    assert "missing_supported_capabilities" in result.issues
