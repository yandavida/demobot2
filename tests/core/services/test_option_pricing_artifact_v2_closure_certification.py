from __future__ import annotations

import pytest
from decimal import Decimal

from core.contracts.option_valuation_result_v2 import OptionValuationResultV2
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1
from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1
from core.contracts.valuation_measure_result_v2 import ValuationMeasureMethodKindV2
from core.contracts.valuation_measure_result_v2 import ValuationMeasureResultV2
from core.contracts.valuation_measure_set_v1 import PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1
from core.contracts.valuation_measure_set_v1 import PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1
from core.services.pricing_artifact_builder_v2 import build_option_pricing_artifact_v2
from core.services.pricing_artifact_export_v2 import export_option_pricing_artifact_payload_v2
from core.services.pricing_artifact_import_v2 import import_option_pricing_artifact_v2_from_canonical_payload


CANONICAL_THETA_REFERENCE = (
    "ThetaRolledFxInputsBoundaryV1:"
    "current_resolved_input_reference=sha256:current;"
    "theta_rolled_resolved_input_reference=sha256:rolled;"
    "theta_roll_policy_id=theta_rolled_resolved_input_1d_calendar_upstream_v1"
)


def _closure_fixture_results() -> tuple[OptionValuationResultV2, OptionValuationResultV2]:
    # Canonical and model-direct fixtures for closure property
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
    numerical: set[ValuationMeasureNameV1] = {
        ValuationMeasureNameV1.DELTA_SPOT_NON_PREMIUM_ADJUSTED,
        ValuationMeasureNameV1.GAMMA_SPOT,
        ValuationMeasureNameV1.VEGA_1VOL_ABS,
        ValuationMeasureNameV1.THETA_1D_CALENDAR,
        ValuationMeasureNameV1.RHO_DOMESTIC_1PCT,
        ValuationMeasureNameV1.RHO_FOREIGN_1PCT,
    }

    canonical_measures = [
        ValuationMeasureResultV2(
            measure_name=measure_name,
            value=values[measure_name],
            method_kind=(
                ValuationMeasureMethodKindV2.NUMERICAL_BUMP_REPRICE
                if measure_name in numerical
                else ValuationMeasureMethodKindV2.MODEL_DIRECT
            ),
            measure_policy_id="phase_d.measure_policy.v2",
            bump_policy_id="phase_d.bump_policy.v1" if measure_name in numerical else None,
            tolerance_policy_id="phase_d.tolerance_policy.v1" if measure_name in numerical else None,
        )
        for measure_name in PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1
    ]

    model_direct_measures = [
        ValuationMeasureResultV2(
            measure_name=measure_name,
            value=Decimal(index + 1),
            method_kind=ValuationMeasureMethodKindV2.MODEL_DIRECT,
            measure_policy_id="phase_d.measure_policy.v2",
        )
        for index, measure_name in enumerate(PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1)
    ]

    canonical_result = OptionValuationResultV2(
        engine_name="american_crr_fx_engine",
        engine_version="1.0.0",
        model_name="crr_recombining_binomial",
        model_version="1.0.0",
        resolved_input_contract_name="ResolvedFxOptionValuationInputsV1",
        resolved_input_contract_version="1.0.0",
        resolved_input_reference="sha256:resolved-current",
        resolved_lattice_policy_contract_name="ResolvedAmericanLatticePolicyV1",
        resolved_lattice_policy_contract_version="1.0.0",
        resolved_lattice_policy_reference=(
            "ResolvedAmericanLatticePolicyV1:model_family_id=american_crr_recombining_binomial_v1;"
            "step_count=250;"
            "early_exercise_policy_id=american_early_exercise_max_with_intrinsic_floor_v1;"
            "convergence_policy_id=american_crr_step_convergence_pr_d_v1;"
            "edge_case_policy_id=american_crr_edge_cases_intrinsic_floor_v1;"
            "bump_policy_id=american_crr_bump_reprice_policy_pr_d_v1;"
            "tolerance_policy_id=american_crr_numerical_tolerance_policy_pr_d_v1"
        ),
        theta_roll_boundary_contract_name=THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1,
        theta_roll_boundary_contract_version=THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1,
        theta_roll_boundary_reference=CANONICAL_THETA_REFERENCE,
        valuation_measures=tuple(canonical_measures),
    )

    model_direct_result = OptionValuationResultV2(
        engine_name="american_crr_fx_engine",
        engine_version="1.0.0",
        model_name="crr_recombining_binomial",
        model_version="1.0.0",
        resolved_input_contract_name="ResolvedFxOptionValuationInputsV1",
        resolved_input_contract_version="1.0.0",
        resolved_input_reference="sha256:resolved-current",
        resolved_lattice_policy_contract_name="ResolvedAmericanLatticePolicyV1",
        resolved_lattice_policy_contract_version="1.0.0",
        resolved_lattice_policy_reference=(
            "ResolvedAmericanLatticePolicyV1:model_family_id=american_crr_recombining_binomial_v1;"
            "step_count=250;"
            "early_exercise_policy_id=american_early_exercise_max_with_intrinsic_floor_v1;"
            "convergence_policy_id=american_crr_step_convergence_pr_d_v1;"
            "edge_case_policy_id=american_crr_edge_cases_intrinsic_floor_v1;"
            "bump_policy_id=american_crr_bump_reprice_policy_pr_d_v1;"
            "tolerance_policy_id=american_crr_numerical_tolerance_policy_pr_d_v1"
        ),
        valuation_measures=tuple(model_direct_measures),
    )

    return (canonical_result, model_direct_result)


_CLOSURE_FIXTURES: tuple[OptionValuationResultV2, OptionValuationResultV2] = _closure_fixture_results()
_CLOSURE_PARAMS: tuple[tuple[OptionValuationResultV2, tuple[ValuationMeasureNameV1, ...], bool], ...] = (
    (_CLOSURE_FIXTURES[0], PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1, True),
    (_CLOSURE_FIXTURES[1], PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1, False),
)


@pytest.mark.parametrize("result_fixture, expected_measure_order, expect_theta_lineage", _CLOSURE_PARAMS)
def test_artifact_v2_export_import_closure_strong(
    result_fixture: OptionValuationResultV2,
    expected_measure_order: tuple[ValuationMeasureNameV1, ...],
    expect_theta_lineage: bool,
) -> None:
    """
    Certifies closure property with explicit field-level assertions for both canonical and model-direct.
    """
    # Step 1: Build artifact from result
    artifact1 = build_option_pricing_artifact_v2(valuation_result=result_fixture)
    # Step 2: Export canonical payload
    payload1 = export_option_pricing_artifact_payload_v2(artifact=artifact1)
    # Step 3: Import artifact from payload
    artifact2 = import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=payload1)
    # Step 4: Export again
    payload2 = export_option_pricing_artifact_payload_v2(artifact=artifact2)
    # Step 5: Build again from imported result
    artifact3 = build_option_pricing_artifact_v2(valuation_result=artifact2.valuation_result)
    payload3 = export_option_pricing_artifact_payload_v2(artifact=artifact3)

    # Assert closure: all artifacts and payloads are byte-identical
    assert artifact1 == artifact2 == artifact3
    assert payload1 == payload2 == payload3

    # Explicit field-level preservation assertions
    for art in (artifact1, artifact2, artifact3):
        measures = art.valuation_result.valuation_measures
        # exact measure-name order
        actual_order = tuple(measure.measure_name for measure in measures)
        assert actual_order == expected_measure_order
        # exact method_kind sequence
        actual_method_kinds = tuple(measure.method_kind for measure in measures)
        expected_method_kinds = tuple(measure.method_kind for measure in result_fixture.valuation_measures)
        assert actual_method_kinds == expected_method_kinds
        # exact measure_policy_id sequence
        actual_policy_ids = tuple(measure.measure_policy_id for measure in measures)
        expected_policy_ids = tuple(measure.measure_policy_id for measure in result_fixture.valuation_measures)
        assert actual_policy_ids == expected_policy_ids
        # exact bump_policy_id sequence
        actual_bump_ids = tuple(measure.bump_policy_id for measure in measures)
        expected_bump_ids = tuple(measure.bump_policy_id for measure in result_fixture.valuation_measures)
        assert actual_bump_ids == expected_bump_ids
        # exact tolerance_policy_id sequence
        actual_tol_ids = tuple(measure.tolerance_policy_id for measure in measures)
        expected_tol_ids = tuple(measure.tolerance_policy_id for measure in result_fixture.valuation_measures)
        assert actual_tol_ids == expected_tol_ids

        # exact theta-lineage behavior by slice
        if expect_theta_lineage:
            assert art.valuation_result.theta_roll_boundary_contract_name == THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1
            assert art.valuation_result.theta_roll_boundary_contract_version == THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1
            assert art.valuation_result.theta_roll_boundary_reference == CANONICAL_THETA_REFERENCE
        else:
            assert art.valuation_result.theta_roll_boundary_contract_name is None
            assert art.valuation_result.theta_roll_boundary_contract_version is None
            assert art.valuation_result.theta_roll_boundary_reference is None

    # Assert contract identity and hash are preserved
    assert artifact2.artifact_contract_name == artifact1.artifact_contract_name
    assert artifact2.artifact_contract_version == artifact1.artifact_contract_version
    assert artifact2.canonical_payload_hash == artifact1.canonical_payload_hash
    # Assert valuation_result is preserved
    assert artifact2.valuation_result == artifact1.valuation_result

    # Guardrail: no forbidden runtime fields in any exported payload
    forbidden = {"timestamp", "uuid", "host", "process", "file_path", "metadata"}
    for payload in (payload1, payload2, payload3):
        for field_name in forbidden:
            assert field_name not in payload


def test_artifact_v2_closure_distinction() -> None:
    """
    Certifies that full canonical and model-direct remain distinct under closure.
    """
    canonical, model_direct = _CLOSURE_FIXTURES
    # Canonical path
    artifact_c = build_option_pricing_artifact_v2(valuation_result=canonical)
    payload_c = export_option_pricing_artifact_payload_v2(artifact=artifact_c)
    imported_c = import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=payload_c)
    # Model-direct path
    artifact_m = build_option_pricing_artifact_v2(valuation_result=model_direct)
    payload_m = export_option_pricing_artifact_payload_v2(artifact=artifact_m)
    imported_m = import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=payload_m)

    # Full canonical remains full canonical
    assert tuple(measure.measure_name for measure in imported_c.valuation_result.valuation_measures) == PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1
    assert imported_c.valuation_result.theta_roll_boundary_contract_name == THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1
    assert imported_c.valuation_result.theta_roll_boundary_contract_version == THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1
    assert imported_c.valuation_result.theta_roll_boundary_reference == CANONICAL_THETA_REFERENCE
    # Model-direct remains model-direct
    assert tuple(measure.measure_name for measure in imported_m.valuation_result.valuation_measures) == PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1
    assert imported_m.valuation_result.theta_roll_boundary_contract_name is None
    # Neither path is normalized into the other
    assert imported_c.valuation_result.valuation_measures != imported_m.valuation_result.valuation_measures


@pytest.mark.parametrize("result_fixture", _CLOSURE_FIXTURES)
def test_artifact_v2_closure_stale_hash_rejection(result_fixture: OptionValuationResultV2) -> None:
    """
    Certifies that closure-level export rejects stale/tampered canonical_payload_hash.
    """
    artifact = build_option_pricing_artifact_v2(valuation_result=result_fixture)
    # Tamper with hash
    tampered = type(artifact)(
        artifact_contract_name=artifact.artifact_contract_name,
        artifact_contract_version=artifact.artifact_contract_version,
        valuation_result=artifact.valuation_result,
        canonical_payload_hash="0" * 64,
    )
    with pytest.raises(ValueError, match="canonical_payload_hash"):
        export_option_pricing_artifact_payload_v2(artifact=tampered)
