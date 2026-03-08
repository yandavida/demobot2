from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable

from core.contracts.model_registry import ModelRegistryEntry
from core.contracts.reference_data_set import ReferenceDataSet
from core.contracts.valuation_policy_set import ValuationPolicySet
from core.contracts.valuation_run import ValuationRun
from core.market_data.market_snapshot_payload_v0 import MarketSnapshotPayloadV0


def _require_non_empty_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    return value


@dataclass(frozen=True)
class ArtifactRecord:
    """Storage-agnostic artifact envelope for repository boundary contracts."""

    artifact_id: str
    valuation_run_id: str
    artifact_type: str
    content_hash: str
    payload_json: str
    created_timestamp: datetime.datetime

    def __post_init__(self) -> None:
        _require_non_empty_string(self.artifact_id, "artifact_id")
        _require_non_empty_string(self.valuation_run_id, "valuation_run_id")
        _require_non_empty_string(self.artifact_type, "artifact_type")
        _require_non_empty_string(self.content_hash, "content_hash")
        _require_non_empty_string(self.payload_json, "payload_json")

        if not isinstance(self.created_timestamp, datetime.datetime):
            raise ValueError("created_timestamp must be a datetime")
        if self.created_timestamp.tzinfo is None:
            raise ValueError("created_timestamp must be timezone-aware")


@runtime_checkable
class MarketSnapshotRepository(Protocol):
    """Persistence boundary for immutable market snapshot artifacts."""

    def get_by_id(self, market_snapshot_id: str) -> Optional[MarketSnapshotPayloadV0]:
        ...

    def save(self, market_snapshot_id: str, market_snapshot: MarketSnapshotPayloadV0) -> None:
        ...


@runtime_checkable
class ReferenceDataSetRepository(Protocol):
    """Persistence boundary for immutable reference data sets."""

    def get_by_id(self, reference_data_set_id: str) -> Optional[ReferenceDataSet]:
        ...

    def save(self, reference_data_set_id: str, reference_data_set: ReferenceDataSet) -> None:
        ...


@runtime_checkable
class ValuationPolicySetRepository(Protocol):
    """Persistence boundary for governed valuation policy sets."""

    def get_by_id(self, valuation_policy_set_id: str) -> Optional[ValuationPolicySet]:
        ...

    def save(self, valuation_policy_set_id: str, valuation_policy_set: ValuationPolicySet) -> None:
        ...


@runtime_checkable
class ValuationRunRepository(Protocol):
    """Persistence boundary for valuation run lineage parents."""

    def get_by_id(self, valuation_run_id: str) -> Optional[ValuationRun]:
        ...

    def save(self, valuation_run: ValuationRun) -> None:
        ...


@runtime_checkable
class ArtifactRepository(Protocol):
    """Persistence boundary for lineage-linked artifacts."""

    def get_by_id(self, artifact_id: str) -> Optional[ArtifactRecord]:
        ...

    def save(self, artifact: ArtifactRecord) -> None:
        ...

    def list_by_valuation_run_id(self, valuation_run_id: str) -> tuple[ArtifactRecord, ...]:
        ...


@runtime_checkable
class ModelRegistryRepository(Protocol):
    """Persistence boundary for governed model metadata entries."""

    def get_by_model_id(self, model_id: str) -> Optional[ModelRegistryEntry]:
        ...

    def save(self, model_entry: ModelRegistryEntry) -> None:
        ...


__all__ = [
    "ArtifactRecord",
    "ArtifactRepository",
    "MarketSnapshotRepository",
    "ModelRegistryRepository",
    "ReferenceDataSetRepository",
    "ValuationPolicySetRepository",
    "ValuationRunRepository",
]
