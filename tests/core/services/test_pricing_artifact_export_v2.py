from __future__ import annotations

import inspect
import json
from decimal import Decimal

import pytest

from core.contracts.canonical_artifact_payload_hash_v2 import canonical_option_pricing_artifact_payload_hash_v2
from core.contracts.canonical_artifact_payload_hash_v2 import canonical_serialize_option_pricing_artifact_payload_v2
from core.contracts.option_valuation_result_v2 import OptionValuationResultV2
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1
from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1
from core.contracts.valuation_measure_result_v2 import ValuationMeasureMethodKindV2
from core.contracts.valuation_measure_result_v2 import ValuationMeasureResultV2
from core.contracts.valuation_measure_set_v1 import PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1
from core.contracts.valuation_measure_set_v1 import PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1
from core.services.pricing_artifact_builder_v2 import build_option_pricing_artifact_v2
from core.services.pricing_artifact_export_v2 import __name__ as export_module_name
from core.services.pricing_artifact_export_v2 import canonical_option_pricing_artifact_payload_from_artifact_v2
from core.services.pricing_artifact_export_v2 import canonical_serialize_option_pricing_artifact_from_artifact_v2
from core.services.pricing_artifact_export_v2 import export_option_pricing_artifact_payload_v2
from core.services.pricing_artifact_export_v2 import validate_option_pricing_artifact_payload_hash_v2


def _full_canonical_result() -> OptionValuationResultV2:
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
        engine_version="1.0.0",
        model_name="crr_recombining_binomial",
        model_version="1.0.0",
        resolved_input_contract_name="ResolvedFxOptionValuationInputsV1",
        resolved_input_contract_version="1.0.0",
        resolved_input_reference="sha256:resolved-current",
        resolved_lattice_policy_contract_name="ResolvedAmericanLatticePolicyV1",
        resolved_lattice_policy_contract_version="1.0.0",
        resolved_lattice_policy_reference="ResolvedAmericanLatticePolicyV1:model_family_id=american_crr_recombining_binomial_v1;step_count=250;early_exercise_policy_id=american_early_exercise_max_with_intrinsic_floor_v1;convergence_policy_id=american_crr_step_convergence_pr_d_v1;edge_case_policy_id=american_crr_edge_cases_intrinsic_floor_v1;bump_policy_id=american_crr_bump_reprice_policy_pr_d_v1;tolerance_policy_id=american_crr_numerical_tolerance_policy_pr_d_v1",
        theta_roll_boundary_contract_name=THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1,
        theta_roll_boundary_contract_version=THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1,
        theta_roll_boundary_reference=(
            "ThetaRolledFxInputsBoundaryV1:"
            "current_resolved_input_reference=sha256:current;"
            "theta_rolled_resolved_input_reference=sha256:rolled;"
            "theta_roll_policy_id=theta_rolled_resolved_input_1d_calendar_upstream_v1"
        ),
        valuation_measures=tuple(measures),
    )


def _model_direct_result() -> OptionValuationResultV2:
    measures = tuple(
        ValuationMeasureResultV2(
            measure_name=measure_name,
            value=Decimal(index + 1),
            method_kind=ValuationMeasureMethodKindV2.MODEL_DIRECT,
            measure_policy_id="phase_d.measure_policy.v2",
        )
        for index, measure_name in enumerate(PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1)
    )
    return OptionValuationResultV2(
        engine_name="american_crr_fx_engine",
        engine_version="1.0.0",
        model_name="crr_recombining_binomial",
        model_version="1.0.0",
        resolved_input_contract_name="ResolvedFxOptionValuationInputsV1",
        resolved_input_contract_version="1.0.0",
        resolved_input_reference="sha256:resolved-current",
        resolved_lattice_policy_contract_name="ResolvedAmericanLatticePolicyV1",
        resolved_lattice_policy_contract_version="1.0.0",
        resolved_lattice_policy_reference="ResolvedAmericanLatticePolicyV1:model_family_id=american_crr_recombining_binomial_v1;step_count=250;early_exercise_policy_id=american_early_exercise_max_with_intrinsic_floor_v1;convergence_policy_id=american_crr_step_convergence_pr_d_v1;edge_case_policy_id=american_crr_edge_cases_intrinsic_floor_v1;bump_policy_id=american_crr_bump_reprice_policy_pr_d_v1;tolerance_policy_id=american_crr_numerical_tolerance_policy_pr_d_v1",
        valuation_measures=measures,
    )


def test_successful_canonical_export_from_full_canonical_artifact() -> None:
    artifact = build_option_pricing_artifact_v2(valuation_result=_full_canonical_result())

    exported = export_option_pricing_artifact_payload_v2(artifact=artifact)

    assert isinstance(exported, str)


def test_successful_canonical_export_from_model_direct_artifact() -> None:
    artifact = build_option_pricing_artifact_v2(valuation_result=_model_direct_result())

    exported = export_option_pricing_artifact_payload_v2(artifact=artifact)

    assert isinstance(exported, str)


def test_exported_serialization_equals_direct_foundation_call() -> None:
    artifact = build_option_pricing_artifact_v2(valuation_result=_full_canonical_result())

    exported = export_option_pricing_artifact_payload_v2(artifact=artifact)
    direct = canonical_serialize_option_pricing_artifact_payload_v2(
        valuation_result=artifact.valuation_result,
    )

    assert exported == direct


def test_repeated_export_for_same_artifact_is_identical() -> None:
    artifact = build_option_pricing_artifact_v2(valuation_result=_full_canonical_result())

    first = export_option_pricing_artifact_payload_v2(artifact=artifact)
    second = export_option_pricing_artifact_payload_v2(artifact=artifact)

    assert first == second


def test_export_rejects_tampered_or_stale_hash() -> None:
    artifact = build_option_pricing_artifact_v2(valuation_result=_full_canonical_result())
    stale_artifact = type(artifact)(
        artifact_contract_name=artifact.artifact_contract_name,
        artifact_contract_version=artifact.artifact_contract_version,
        valuation_result=artifact.valuation_result,
        canonical_payload_hash="0" * 64,
    )

    with pytest.raises(ValueError, match="canonical_payload_hash"):
        export_option_pricing_artifact_payload_v2(artifact=stale_artifact)


def test_validation_passes_when_stored_hash_matches_recomputed_hash() -> None:
    artifact = build_option_pricing_artifact_v2(valuation_result=_full_canonical_result())

    computed = validate_option_pricing_artifact_payload_hash_v2(artifact=artifact)

    assert computed == artifact.canonical_payload_hash


def test_validation_rejects_tampered_or_stale_hash() -> None:
    valuation_result = _full_canonical_result()
    artifact = build_option_pricing_artifact_v2(valuation_result=valuation_result)

    stale_artifact = type(artifact)(
        artifact_contract_name=artifact.artifact_contract_name,
        artifact_contract_version=artifact.artifact_contract_version,
        valuation_result=artifact.valuation_result,
        canonical_payload_hash="0" * 64,
    )

    with pytest.raises(ValueError, match="canonical_payload_hash"):
        validate_option_pricing_artifact_payload_hash_v2(artifact=stale_artifact)


def test_validation_rejects_wrong_input_type() -> None:
    with pytest.raises(ValueError, match="OptionPricingArtifactV2"):
        validate_option_pricing_artifact_payload_hash_v2(artifact={})  # type: ignore[arg-type]


def test_theta_lineage_preserved_for_full_canonical_artifact_export() -> None:
    artifact = build_option_pricing_artifact_v2(valuation_result=_full_canonical_result())

    exported_payload = json.loads(export_option_pricing_artifact_payload_v2(artifact=artifact))

    assert exported_payload["theta_roll_boundary_contract_name"] == THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1
    assert exported_payload["theta_roll_boundary_contract_version"] == THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1
    assert exported_payload["theta_roll_boundary_reference"] == (
        "ThetaRolledFxInputsBoundaryV1:"
        "current_resolved_input_reference=sha256:current;"
        "theta_rolled_resolved_input_reference=sha256:rolled;"
        "theta_roll_policy_id=theta_rolled_resolved_input_1d_calendar_upstream_v1"
    )


def test_no_theta_lineage_synthesized_for_model_direct_artifact_export() -> None:
    artifact = build_option_pricing_artifact_v2(valuation_result=_model_direct_result())

    exported_payload = json.loads(export_option_pricing_artifact_payload_v2(artifact=artifact))

    assert exported_payload["theta_roll_boundary_contract_name"] is None
    assert exported_payload["theta_roll_boundary_contract_version"] is None
    assert exported_payload["theta_roll_boundary_reference"] is None


def test_canonical_measure_order_preserved_in_exported_serialization() -> None:
    artifact = build_option_pricing_artifact_v2(valuation_result=_full_canonical_result())

    exported_payload = json.loads(export_option_pricing_artifact_payload_v2(artifact=artifact))
    names = tuple(item["measure_name"] for item in exported_payload["valuation_measures"])

    assert names == tuple(item.value for item in PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1)


def test_no_forbidden_runtime_fields_in_exported_serialization() -> None:
    artifact = build_option_pricing_artifact_v2(valuation_result=_full_canonical_result())

    exported = export_option_pricing_artifact_payload_v2(artifact=artifact)
    forbidden = {
        "timestamp",
        "uuid",
        "host",
        "process",
        "file_path",
        "metadata",
    }

    for item in forbidden:
        assert item not in exported


def test_export_module_has_no_hidden_resolver_runtime_pricing_or_persistence_imports() -> None:
    module = __import__(export_module_name, fromlist=["*"])
    source = inspect.getsource(module)

    assert "datetime" not in source
    assert "uuid" not in source
    assert "option_valuation_input_resolver_v1" not in source
    assert "crr_american_fx_kernel_v1" not in source
    assert "AmericanCrrFxEngineV1" not in source
    assert "core.persistence" not in source


def test_payload_derivation_function_matches_foundation() -> None:
    artifact = build_option_pricing_artifact_v2(valuation_result=_full_canonical_result())

    derived = canonical_option_pricing_artifact_payload_from_artifact_v2(artifact=artifact)
    direct_hash = canonical_option_pricing_artifact_payload_hash_v2(valuation_result=artifact.valuation_result)

    assert canonical_option_pricing_artifact_payload_hash_v2(valuation_result=artifact.valuation_result) == direct_hash
    assert canonical_serialize_option_pricing_artifact_from_artifact_v2(artifact=artifact) == canonical_serialize_option_pricing_artifact_payload_v2(
        valuation_result=artifact.valuation_result,
    )
    assert isinstance(derived, dict)
