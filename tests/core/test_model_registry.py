from __future__ import annotations

import datetime
from dataclasses import FrozenInstanceError
from dataclasses import fields

import pytest

from core.contracts.model_registry import ModelCapability
from core.contracts.model_registry import ModelRegistryEntry


def _capability() -> ModelCapability:
    return ModelCapability(
        instrument_family="fx_option_vanilla",
        exercise_style="european",
        measure="pv",
    )


def _entry(**overrides) -> ModelRegistryEntry:
    payload = {
        "model_id": "model.fx.bs.v1",
        "semantic_version": "1.0.0",
        "implementation_version": "impl-2026-03-08",
        "validation_status": "approved",
        "owner": "treasury_model_risk",
        "approval_date": datetime.date(2026, 3, 8),
        "benchmark_pack_id": "bench.fx.options.v1",
        "known_limitations": ["european-only"],
        "numeric_policy_id": "numeric.policy.v1",
        "supported_capabilities": [_capability()],
    }
    payload.update(overrides)
    return ModelRegistryEntry(**payload)


def test_model_registry_entry_construction() -> None:
    entry = _entry()

    assert entry.model_id == "model.fx.bs.v1"
    assert entry.validation_status == "approved"
    assert entry.supported_capabilities[0].measure == "pv"


def test_model_registry_entry_is_immutable() -> None:
    entry = _entry()

    with pytest.raises(FrozenInstanceError):
        entry.owner = "new_owner"


def test_model_registry_entry_requires_all_fields() -> None:
    with pytest.raises(TypeError):
        ModelRegistryEntry(
            model_id="model.fx.bs.v1",
            semantic_version="1.0.0",
            implementation_version="impl-2026-03-08",
            validation_status="approved",
            owner="treasury_model_risk",
            approval_date=datetime.date(2026, 3, 8),
            benchmark_pack_id="bench.fx.options.v1",
            known_limitations=("european-only",),
            numeric_policy_id="numeric.policy.v1",
        )


def test_model_registry_entry_has_governance_capability_fields() -> None:
    names = {field.name for field in fields(ModelRegistryEntry)}

    assert "validation_status" in names
    assert "benchmark_pack_id" in names
    assert "numeric_policy_id" in names
    assert "supported_capabilities" in names


def test_model_registry_entry_has_no_engine_or_output_payload_fields() -> None:
    names = {field.name for field in fields(ModelRegistryEntry)}

    forbidden_substrings = ("engine_impl", "pricing_output", "risk_output", "payload")
    assert not any(any(token in name for token in forbidden_substrings) for name in names)
