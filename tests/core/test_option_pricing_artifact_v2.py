from __future__ import annotations

from dataclasses import FrozenInstanceError
from dataclasses import fields
from decimal import Decimal

import pytest

from core.contracts.option_pricing_artifact_v1 import OptionPricingArtifactV1
from core.contracts.option_pricing_artifact_v2 import ARTIFACT_CONTRACT_NAME_V2
from core.contracts.option_pricing_artifact_v2 import ARTIFACT_CONTRACT_VERSION_V2
from core.contracts.option_pricing_artifact_v2 import OptionPricingArtifactV2
from core.contracts.option_valuation_result_v2 import OptionValuationResultV2
from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1
from core.contracts.valuation_measure_result_v2 import ValuationMeasureMethodKindV2
from core.contracts.valuation_measure_result_v2 import ValuationMeasureResultV2
from core.contracts.valuation_measure_set_v1 import PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1


def _valuation_result_v2() -> OptionValuationResultV2:
    values: dict[ValuationMeasureNameV1, Decimal] = {
        ValuationMeasureNameV1.PRESENT_VALUE: Decimal("100.00"),
        ValuationMeasureNameV1.INTRINSIC_VALUE: Decimal("10.00"),
        ValuationMeasureNameV1.TIME_VALUE: Decimal("90.00"),
        ValuationMeasureNameV1.DELTA_SPOT_NON_PREMIUM_ADJUSTED: Decimal("0.45"),
        ValuationMeasureNameV1.GAMMA_SPOT: Decimal("0.02"),
        ValuationMeasureNameV1.VEGA_1VOL_ABS: Decimal("1.25"),
        ValuationMeasureNameV1.THETA_1D_CALENDAR: Decimal("-0.15"),
        ValuationMeasureNameV1.RHO_DOMESTIC_1PCT: Decimal("0.80"),
        ValuationMeasureNameV1.RHO_FOREIGN_1PCT: Decimal("-0.75"),
    }
    numerical_measures = {
        ValuationMeasureNameV1.DELTA_SPOT_NON_PREMIUM_ADJUSTED,
        ValuationMeasureNameV1.GAMMA_SPOT,
        ValuationMeasureNameV1.VEGA_1VOL_ABS,
        ValuationMeasureNameV1.THETA_1D_CALENDAR,
        ValuationMeasureNameV1.RHO_DOMESTIC_1PCT,
        ValuationMeasureNameV1.RHO_FOREIGN_1PCT,
    }

    measures: list[ValuationMeasureResultV2] = []
    for measure_name in PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1:
        if measure_name in numerical_measures:
            measures.append(
                ValuationMeasureResultV2(
                    measure_name=measure_name,
                    value=values[measure_name],
                    method_kind=ValuationMeasureMethodKindV2.NUMERICAL_BUMP_REPRICE,
                    measure_policy_id="phase_d.measure_policy.v2",
                    bump_policy_id="phase_d.bump_policy.v1",
                    tolerance_policy_id="phase_d.tolerance_policy.v1",
                )
            )
        else:
            measures.append(
                ValuationMeasureResultV2(
                    measure_name=measure_name,
                    value=values[measure_name],
                    method_kind=ValuationMeasureMethodKindV2.MODEL_DIRECT,
                    measure_policy_id="phase_d.measure_policy.v2",
                )
            )

    return OptionValuationResultV2(
        engine_name="american_crr_fx_engine",
        engine_version="2.0.0",
        model_name="crr_recombining_binomial",
        model_version="1.0.0",
        resolved_input_contract_name="ResolvedFxOptionValuationInputsV1",
        resolved_input_contract_version="1.0.0",
        resolved_input_reference="resolved-input-ref-2027-01-01-run-001",
        resolved_lattice_policy_contract_name="ResolvedAmericanLatticePolicyV1",
        resolved_lattice_policy_contract_version="1.0.0",
        resolved_lattice_policy_reference="resolved-lattice-policy-ref-2027-01-01-run-001",
        theta_roll_boundary_contract_name="ThetaRolledFxInputsBoundaryV1",
        theta_roll_boundary_contract_version="1.0.0",
        theta_roll_boundary_reference=(
            "ThetaRolledFxInputsBoundaryV1:"
            "current_resolved_input_reference=sha256:current;"
            "theta_rolled_resolved_input_reference=sha256:rolled;"
            "theta_roll_policy_id=theta_rolled_resolved_input_1d_calendar_upstream_v1"
        ),
        valuation_measures=tuple(measures),
    )


def test_v2_artifact_field_shape_is_explicit_and_minimal() -> None:
    assert [field.name for field in fields(OptionPricingArtifactV2)] == [
        "artifact_contract_name",
        "artifact_contract_version",
        "valuation_result",
        "canonical_payload_hash",
    ]


def test_v2_artifact_is_immutable() -> None:
    artifact = OptionPricingArtifactV2(
        artifact_contract_name=ARTIFACT_CONTRACT_NAME_V2,
        artifact_contract_version=ARTIFACT_CONTRACT_VERSION_V2,
        valuation_result=_valuation_result_v2(),
        canonical_payload_hash="a" * 64,
    )

    with pytest.raises(FrozenInstanceError):
        artifact.canonical_payload_hash = "b" * 64  # type: ignore[misc]


def test_v1_artifact_contract_shape_remains_frozen() -> None:
    assert [field.name for field in fields(OptionPricingArtifactV1)] == [
        "artifact_contract_name",
        "artifact_contract_version",
        "valuation_result",
        "canonical_payload_hash",
    ]


def test_v2_artifact_minimalism_guard_no_future_or_runtime_semantics() -> None:
    forbidden = {
        "portfolio",
        "scenario",
        "basket",
        "lifecycle",
        "advisory",
        "metadata",
        "timestamp",
        "uuid",
        "storage",
        "api",
    }
    field_names = {field.name for field in fields(OptionPricingArtifactV2)}

    assert field_names.isdisjoint(forbidden)


def test_v2_artifact_requires_v2_result_payload_and_preserves_second_input_traceability() -> None:
    valuation_result = _valuation_result_v2()
    artifact = OptionPricingArtifactV2(
        artifact_contract_name=ARTIFACT_CONTRACT_NAME_V2,
        artifact_contract_version=ARTIFACT_CONTRACT_VERSION_V2,
        valuation_result=valuation_result,
        canonical_payload_hash="c" * 64,
    )

    assert artifact.valuation_result.resolved_input_contract_name == "ResolvedFxOptionValuationInputsV1"
    assert artifact.valuation_result.resolved_input_reference == "resolved-input-ref-2027-01-01-run-001"
    assert artifact.valuation_result.resolved_lattice_policy_contract_name == "ResolvedAmericanLatticePolicyV1"
    assert artifact.valuation_result.resolved_lattice_policy_contract_version == "1.0.0"
    assert artifact.valuation_result.resolved_lattice_policy_reference == "resolved-lattice-policy-ref-2027-01-01-run-001"
    assert artifact.valuation_result.theta_roll_boundary_contract_name == "ThetaRolledFxInputsBoundaryV1"
    assert artifact.valuation_result.theta_roll_boundary_contract_version == "1.0.0"
    assert artifact.valuation_result.theta_roll_boundary_reference == (
        "ThetaRolledFxInputsBoundaryV1:"
        "current_resolved_input_reference=sha256:current;"
        "theta_rolled_resolved_input_reference=sha256:rolled;"
        "theta_roll_policy_id=theta_rolled_resolved_input_1d_calendar_upstream_v1"
    )
    assert artifact.valuation_result is valuation_result

    with pytest.raises(ValueError, match="valuation_result"):
        OptionPricingArtifactV2(
            artifact_contract_name="OptionPricingArtifactV2",
            artifact_contract_version="2.0.0",
            valuation_result="not-a-v2-result",  # type: ignore[arg-type]
            canonical_payload_hash="d" * 64,
        )


def test_v2_artifact_identity_and_hash_shape_are_explicit_and_deterministic() -> None:
    with pytest.raises(ValueError, match="artifact_contract_name"):
        OptionPricingArtifactV2(
            artifact_contract_name="",
            artifact_contract_version=ARTIFACT_CONTRACT_VERSION_V2,
            valuation_result=_valuation_result_v2(),
            canonical_payload_hash="e" * 64,
        )

    with pytest.raises(ValueError, match="artifact_contract_version"):
        OptionPricingArtifactV2(
            artifact_contract_name=ARTIFACT_CONTRACT_NAME_V2,
            artifact_contract_version="",
            valuation_result=_valuation_result_v2(),
            canonical_payload_hash="f" * 64,
        )

    with pytest.raises(ValueError, match="canonical_payload_hash"):
        OptionPricingArtifactV2(
            artifact_contract_name=ARTIFACT_CONTRACT_NAME_V2,
            artifact_contract_version=ARTIFACT_CONTRACT_VERSION_V2,
            valuation_result=_valuation_result_v2(),
            canonical_payload_hash="abc",
        )


def test_v2_artifact_rejects_wrong_contract_identity_values() -> None:
    with pytest.raises(ValueError, match="artifact_contract_name"):
        OptionPricingArtifactV2(
            artifact_contract_name="OptionPricingArtifactV3",
            artifact_contract_version=ARTIFACT_CONTRACT_VERSION_V2,
            valuation_result=_valuation_result_v2(),
            canonical_payload_hash="1" * 64,
        )

    with pytest.raises(ValueError, match="artifact_contract_version"):
        OptionPricingArtifactV2(
            artifact_contract_name=ARTIFACT_CONTRACT_NAME_V2,
            artifact_contract_version="2.1.0",
            valuation_result=_valuation_result_v2(),
            canonical_payload_hash="2" * 64,
        )


def test_v2_artifact_identity_constants_are_stable_and_non_empty() -> None:
    assert ARTIFACT_CONTRACT_NAME_V2 == "OptionPricingArtifactV2"
    assert ARTIFACT_CONTRACT_VERSION_V2 == "2.0.0"

    assert isinstance(ARTIFACT_CONTRACT_NAME_V2, str)
    assert isinstance(ARTIFACT_CONTRACT_VERSION_V2, str)
    assert ARTIFACT_CONTRACT_NAME_V2
    assert ARTIFACT_CONTRACT_VERSION_V2