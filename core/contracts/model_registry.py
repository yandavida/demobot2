from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Iterable


ALLOWED_VALIDATION_STATUSES = {
    "approved",
    "provisional",
    "deprecated",
    "retired",
}


def _require_non_empty_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    return value


def _normalize_limitations(values: Iterable[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    for limitation in values:
        normalized.append(_require_non_empty_string(limitation, "known_limitations entry"))
    return tuple(normalized)


@dataclass(frozen=True)
class ModelCapability:
    """Auditable capability descriptor for governed model approval scope."""

    instrument_family: str
    exercise_style: str
    measure: str

    def __post_init__(self) -> None:
        _require_non_empty_string(self.instrument_family, "instrument_family")
        _require_non_empty_string(self.exercise_style, "exercise_style")
        _require_non_empty_string(self.measure, "measure")


@dataclass(frozen=True)
class ModelRegistryEntry:
    """Canonical governance metadata entry for approved valuation model use."""

    model_id: str
    semantic_version: str
    implementation_version: str
    validation_status: str
    owner: str
    approval_date: datetime.date
    benchmark_pack_id: str
    known_limitations: tuple[str, ...]
    numeric_policy_id: str
    supported_capabilities: tuple[ModelCapability, ...]

    def __post_init__(self) -> None:
        _require_non_empty_string(self.model_id, "model_id")
        _require_non_empty_string(self.semantic_version, "semantic_version")
        _require_non_empty_string(self.implementation_version, "implementation_version")
        _require_non_empty_string(self.owner, "owner")
        _require_non_empty_string(self.benchmark_pack_id, "benchmark_pack_id")
        _require_non_empty_string(self.numeric_policy_id, "numeric_policy_id")

        if self.validation_status not in ALLOWED_VALIDATION_STATUSES:
            allowed = sorted(ALLOWED_VALIDATION_STATUSES)
            raise ValueError(f"validation_status must be one of {allowed}")

        if not isinstance(self.approval_date, datetime.date):
            raise ValueError("approval_date must be a date")

        object.__setattr__(self, "known_limitations", _normalize_limitations(self.known_limitations))

        if len(self.supported_capabilities) == 0:
            raise ValueError("supported_capabilities must not be empty")
        normalized_capabilities: list[ModelCapability] = []
        for capability in self.supported_capabilities:
            if not isinstance(capability, ModelCapability):
                raise ValueError("supported_capabilities entries must be ModelCapability")
            normalized_capabilities.append(capability)
        object.__setattr__(self, "supported_capabilities", tuple(normalized_capabilities))


__all__ = [
    "ALLOWED_VALIDATION_STATUSES",
    "ModelCapability",
    "ModelRegistryEntry",
]
