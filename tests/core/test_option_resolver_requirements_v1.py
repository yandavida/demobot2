from __future__ import annotations

import datetime
from dataclasses import FrozenInstanceError

import pytest

from core.contracts.model_registry import ModelCapability
from core.contracts.model_registry import ModelRegistryEntry
from core.contracts.option_resolver_requirements_v1 import FxOptionValuationRequirementsV1
from core.contracts.option_resolver_requirements_v1 import OptionValuationRequirementsV1


def _model_registry_entry_with_option_capabilities() -> ModelRegistryEntry:
    return ModelRegistryEntry(
        model_id="model.fx.option.v1",
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
            ModelCapability(
                instrument_family="fx_option_vanilla",
                exercise_style="european",
                measure="delta",
            ),
        ),
    )


def test_option_requirements_construct_with_explicit_dimensions() -> None:
    requirements = OptionValuationRequirementsV1(
        instrument_family="fx_option_vanilla",
        payoff_family="vanilla",
        option_type="call",
        exercise_style="european",
        requested_measures=("PV", "Delta"),
        required_market_inputs=("spot", "vol_surface"),
    )

    assert requirements.instrument_family == "fx_option_vanilla"
    assert requirements.payoff_family == "vanilla"
    assert requirements.option_type == "call"
    assert requirements.exercise_style == "european"
    assert requirements.requested_measures == ("pv", "delta")
    assert requirements.required_market_inputs == ("spot", "vol_surface")


def test_fx_option_requirements_include_settlement_dimension() -> None:
    requirements = FxOptionValuationRequirementsV1(
        instrument_family="fx_option_vanilla",
        payoff_family="vanilla",
        option_type="put",
        exercise_style="european",
        settlement_style="Deliverable",
        requested_measures=("pv",),
        required_market_inputs=("spot", "domestic_curve", "foreign_curve", "vol_surface"),
    )

    assert requirements.settlement_style == "deliverable"


def test_requirements_are_immutable() -> None:
    requirements = OptionValuationRequirementsV1(
        instrument_family="fx_option_vanilla",
        payoff_family="vanilla",
        option_type="call",
        exercise_style="european",
        requested_measures=("pv",),
        required_market_inputs=("spot",),
    )

    with pytest.raises(FrozenInstanceError):
        requirements.option_type = "put"


def test_rejects_invalid_structural_values() -> None:
    with pytest.raises(ValueError, match="requested_measures"):
        OptionValuationRequirementsV1(
            instrument_family="fx_option_vanilla",
            payoff_family="vanilla",
            option_type="call",
            exercise_style="european",
            requested_measures=(),
            required_market_inputs=("spot",),
        )

    with pytest.raises(ValueError, match="requested_measures"):
        OptionValuationRequirementsV1(
            instrument_family="fx_option_vanilla",
            payoff_family="vanilla",
            option_type="call",
            exercise_style="european",
            requested_measures=("pv", "PV"),
            required_market_inputs=("spot",),
        )

    with pytest.raises(ValueError, match="option_type"):
        OptionValuationRequirementsV1(
            instrument_family="fx_option_vanilla",
            payoff_family="vanilla",
            option_type="digital",
            exercise_style="european",
            requested_measures=("pv",),
            required_market_inputs=("spot",),
        )

    with pytest.raises(ValueError, match="settlement_style"):
        FxOptionValuationRequirementsV1(
            instrument_family="fx_option_vanilla",
            payoff_family="vanilla",
            option_type="call",
            exercise_style="european",
            settlement_style="cash",
            requested_measures=("pv",),
            required_market_inputs=("spot",),
        )


def test_required_capabilities_align_with_model_registry_supported_capabilities() -> None:
    entry = _model_registry_entry_with_option_capabilities()
    requirements = OptionValuationRequirementsV1(
        instrument_family="fx_option_vanilla",
        payoff_family="vanilla",
        option_type="call",
        exercise_style="european",
        requested_measures=("pv", "delta"),
        required_market_inputs=("spot", "vol_surface"),
    )

    required = set(requirements.required_capabilities())
    supported = set(entry.supported_capabilities)

    assert required.issubset(supported)


def test_rejects_unrelated_payload_fields() -> None:
    with pytest.raises(TypeError):
        OptionValuationRequirementsV1(
            instrument_family="fx_option_vanilla",
            payoff_family="vanilla",
            option_type="call",
            exercise_style="european",
            requested_measures=("pv",),
            required_market_inputs=("spot",),
            pricing_engine_id="bs.v1",
        )
