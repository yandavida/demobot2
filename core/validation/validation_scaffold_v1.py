from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from core.contracts.model_registry import ModelRegistryEntry


@dataclass(frozen=True)
class ArtifactSchemaRefV1:
    """Explicit schema/version pair for artifact discipline checks."""

    schema_name: str
    schema_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.schema_name, str) or not self.schema_name.strip():
            raise ValueError("schema_name must be a non-empty string")
        if not isinstance(self.schema_version, str) or not self.schema_version.strip():
            raise ValueError("schema_version must be a non-empty string")


def parse_artifact_schema_ref_v1(payload: Mapping[str, object]) -> ArtifactSchemaRefV1:
    """Parse schema/version fields from an artifact-like mapping."""

    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")

    schema_name = payload.get("schema_name")
    schema_version = payload.get("schema_version")

    if not isinstance(schema_name, str) or not schema_name.strip():
        raise ValueError("schema_name must be present and non-empty")
    if not isinstance(schema_version, str) or not schema_version.strip():
        raise ValueError("schema_version must be present and non-empty")

    return ArtifactSchemaRefV1(
        schema_name=schema_name,
        schema_version=schema_version,
    )


def ensure_expected_artifact_schema_v1(
    schema_ref: ArtifactSchemaRefV1,
    *,
    expected_schema_name: str,
    expected_schema_version: str,
) -> None:
    """Enforce explicit expected artifact schema name/version."""

    if schema_ref.schema_name != expected_schema_name:
        raise ValueError("artifact schema_name does not match expected value")
    if schema_ref.schema_version != expected_schema_version:
        raise ValueError("artifact schema_version does not match expected value")


@dataclass(frozen=True)
class BenchmarkCaseV1:
    """Minimal benchmark-case contract for deterministic harness scaffolding."""

    case_id: str
    model_id: str
    benchmark_pack_id: str
    valuation_run_id: str

    def __post_init__(self) -> None:
        for name in ("case_id", "model_id", "benchmark_pack_id", "valuation_run_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True)
class BenchmarkResultV1:
    """Deterministic benchmark result shape for governance scaffolding."""

    case_id: str
    is_match: bool
    expected_hash: str
    observed_hash: str


def run_benchmark_case_v1(
    case: BenchmarkCaseV1,
    *,
    expected_hash: str,
    observed_hash: str,
) -> BenchmarkResultV1:
    """Deterministic benchmark harness stub based on hash comparison."""

    if not isinstance(expected_hash, str) or not expected_hash.strip():
        raise ValueError("expected_hash must be a non-empty string")
    if not isinstance(observed_hash, str) or not observed_hash.strip():
        raise ValueError("observed_hash must be a non-empty string")

    return BenchmarkResultV1(
        case_id=case.case_id,
        is_match=(observed_hash == expected_hash),
        expected_hash=expected_hash,
        observed_hash=observed_hash,
    )


@dataclass(frozen=True)
class ReplayCaseV1:
    """Minimal replay-case contract tied to ValuationRun lineage."""

    replay_id: str
    valuation_run_id: str
    artifact_id: str

    def __post_init__(self) -> None:
        for name in ("replay_id", "valuation_run_id", "artifact_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True)
class ReplayDeterminismResultV1:
    replay_id: str
    is_deterministic: bool
    first_hash: str
    second_hash: str


def check_replay_determinism_v1(
    case: ReplayCaseV1,
    *,
    first_hash: str,
    second_hash: str,
) -> ReplayDeterminismResultV1:
    """Deterministic replay scaffold: compare two replay output hashes."""

    if not isinstance(first_hash, str) or not first_hash.strip():
        raise ValueError("first_hash must be a non-empty string")
    if not isinstance(second_hash, str) or not second_hash.strip():
        raise ValueError("second_hash must be a non-empty string")

    return ReplayDeterminismResultV1(
        replay_id=case.replay_id,
        is_deterministic=(first_hash == second_hash),
        first_hash=first_hash,
        second_hash=second_hash,
    )


@dataclass(frozen=True)
class EngineApprovalCheckResultV1:
    model_id: str
    is_approved: bool
    issues: tuple[str, ...]


def check_engine_approval_metadata_v1(entry: ModelRegistryEntry) -> EngineApprovalCheckResultV1:
    """Narrow governance check for required approval metadata signals."""

    issues: list[str] = []

    if entry.validation_status != "approved":
        issues.append("validation_status_not_approved")
    if not entry.benchmark_pack_id.strip():
        issues.append("missing_benchmark_pack_id")
    if not entry.numeric_policy_id.strip():
        issues.append("missing_numeric_policy_id")
    if len(entry.supported_capabilities) == 0:
        issues.append("missing_supported_capabilities")

    return EngineApprovalCheckResultV1(
        model_id=entry.model_id,
        is_approved=(len(issues) == 0),
        issues=tuple(issues),
    )


__all__ = [
    "ArtifactSchemaRefV1",
    "BenchmarkCaseV1",
    "BenchmarkResultV1",
    "EngineApprovalCheckResultV1",
    "ReplayCaseV1",
    "ReplayDeterminismResultV1",
    "check_engine_approval_metadata_v1",
    "check_replay_determinism_v1",
    "ensure_expected_artifact_schema_v1",
    "parse_artifact_schema_ref_v1",
    "run_benchmark_case_v1",
]
