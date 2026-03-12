from __future__ import annotations

import json
import pytest
from decimal import Decimal
from dataclasses import fields

from core.contracts.canonical_artifact_payload_hash_v2 import canonical_option_pricing_artifact_payload_hash_v2
from core.contracts.option_pricing_artifact_v2 import ARTIFACT_CONTRACT_NAME_V2, ARTIFACT_CONTRACT_VERSION_V2, OptionPricingArtifactV2
from core.contracts.option_valuation_result_v2 import OptionValuationResultV2
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1, THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1
from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1
from core.contracts.valuation_measure_result_v2 import ValuationMeasureMethodKindV2, ValuationMeasureResultV2
from core.contracts.valuation_measure_set_v1 import PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1, PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1
from core.services.pricing_artifact_builder_v2 import build_option_pricing_artifact_v2
from core.services.pricing_artifact_export_v2 import export_option_pricing_artifact_payload_v2
from core.services.pricing_artifact_import_v2 import import_option_pricing_artifact_v2_from_canonical_payload


def _full_canonical_result() -> OptionValuationResultV2:
    values = {
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
    numerical = {
        ValuationMeasureNameV1.DELTA_SPOT_NON_PREMIUM_ADJUSTED,
        ValuationMeasureNameV1.GAMMA_SPOT,
        ValuationMeasureNameV1.VEGA_1VOL_ABS,
        ValuationMeasureNameV1.THETA_1D_CALENDAR,
        ValuationMeasureNameV1.RHO_DOMESTIC_1PCT,
        ValuationMeasureNameV1.RHO_FOREIGN_1PCT,
    }
    measures = [
        ValuationMeasureResultV2(
            measure_name=m,
            value=values[m],
            method_kind=ValuationMeasureMethodKindV2.NUMERICAL_BUMP_REPRICE if m in numerical else ValuationMeasureMethodKindV2.MODEL_DIRECT,
            measure_policy_id="phase_d.measure_policy.v2",
            bump_policy_id="phase_d.bump_policy.v1" if m in numerical else None,
            tolerance_policy_id="phase_d.tolerance_policy.v1" if m in numerical else None,
        ) for m in PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1
    ]
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
        theta_roll_boundary_reference="ThetaRolledFxInputsBoundaryV1:current_resolved_input_reference=sha256:current;theta_rolled_resolved_input_reference=sha256:rolled;theta_roll_policy_id=theta_rolled_resolved_input_1d_calendar_upstream_v1",
        valuation_measures=tuple(measures),
    )

def _model_direct_result() -> OptionValuationResultV2:
    measures = tuple(
        ValuationMeasureResultV2(
            measure_name=m,
            value=Decimal(i + 1),
            method_kind=ValuationMeasureMethodKindV2.MODEL_DIRECT,
            measure_policy_id="phase_d.measure_policy.v2",
        ) for i, m in enumerate(PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1)
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

def test_full_canonical_roundtrip_is_byte_identical() -> None:
    result = _full_canonical_result()
    artifact = build_option_pricing_artifact_v2(valuation_result=result)
    payload1 = export_option_pricing_artifact_payload_v2(artifact=artifact)
    imported = import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=payload1)
    payload2 = export_option_pricing_artifact_payload_v2(artifact=imported)
    assert payload1 == payload2
    assert imported.valuation_result == artifact.valuation_result
    assert imported.artifact_contract_name == ARTIFACT_CONTRACT_NAME_V2
    assert imported.artifact_contract_version == ARTIFACT_CONTRACT_VERSION_V2
    assert imported.canonical_payload_hash == canonical_option_pricing_artifact_payload_hash_v2(valuation_result=imported.valuation_result)
    forbidden = {"timestamp", "uuid", "host", "process", "file_path", "metadata"}
    for k in forbidden:
        assert k not in payload2
    # theta lineage must be preserved
    assert imported.valuation_result.theta_roll_boundary_contract_name == THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1
    assert imported.valuation_result.theta_roll_boundary_contract_version == THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1
    assert imported.valuation_result.theta_roll_boundary_reference is not None

def test_model_direct_roundtrip_is_byte_identical() -> None:
    result = _model_direct_result()
    artifact = build_option_pricing_artifact_v2(valuation_result=result)
    payload1 = export_option_pricing_artifact_payload_v2(artifact=artifact)
    imported = import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=payload1)
    payload2 = export_option_pricing_artifact_payload_v2(artifact=imported)
    assert payload1 == payload2
    assert imported.valuation_result == artifact.valuation_result
    assert imported.artifact_contract_name == ARTIFACT_CONTRACT_NAME_V2
    assert imported.artifact_contract_version == ARTIFACT_CONTRACT_VERSION_V2
    assert imported.canonical_payload_hash == canonical_option_pricing_artifact_payload_hash_v2(valuation_result=imported.valuation_result)
    forbidden = {"timestamp", "uuid", "host", "process", "file_path", "metadata"}
    for k in forbidden:
        assert k not in payload2
    # theta lineage must be absent
    assert imported.valuation_result.theta_roll_boundary_contract_name is None
    assert imported.valuation_result.theta_roll_boundary_contract_version is None
    assert imported.valuation_result.theta_roll_boundary_reference is None



@pytest.mark.parametrize("fixture_func, expected_measure_order, expect_theta_lineage", [
    (_full_canonical_result, PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1, True),
    (_model_direct_result, PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1, False),
])
def test_repeated_roundtrip_is_deterministic_and_preserves_invariants(fixture_func, expected_measure_order, expect_theta_lineage) -> None:
    for _ in range(3):
        # Step 1: create governed valuation result
        result = fixture_func()
        # Step 2: build artifact
        artifact = build_option_pricing_artifact_v2(valuation_result=result)
        # Step 3: export payload
        payload1 = export_option_pricing_artifact_payload_v2(artifact=artifact)
        # Step 4: import artifact from payload
        imported = import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=payload1)
        # Step 5: export again
        payload2 = export_option_pricing_artifact_payload_v2(artifact=imported)
        # Step 6: assert byte-identical exported payload
        assert payload1 == payload2
        # Step 7: assert recomputed canonical hash equality
        assert imported.canonical_payload_hash == canonical_option_pricing_artifact_payload_hash_v2(valuation_result=imported.valuation_result)

        # Explicit preservation assertions
        # a. measure-name order
        actual_order = tuple(m.measure_name for m in imported.valuation_result.valuation_measures)
        assert actual_order == expected_measure_order
        # b. method_kind sequence
        actual_method_kinds = tuple(m.method_kind for m in imported.valuation_result.valuation_measures)
        expected_method_kinds = tuple(m.method_kind for m in result.valuation_measures)
        assert actual_method_kinds == expected_method_kinds
        # c. measure_policy_id sequence
        actual_policy_ids = tuple(m.measure_policy_id for m in imported.valuation_result.valuation_measures)
        expected_policy_ids = tuple(m.measure_policy_id for m in result.valuation_measures)
        assert actual_policy_ids == expected_policy_ids
        # d. bump_policy_id sequence
        actual_bump_ids = tuple(m.bump_policy_id for m in imported.valuation_result.valuation_measures)
        expected_bump_ids = tuple(m.bump_policy_id for m in result.valuation_measures)
        assert actual_bump_ids == expected_bump_ids
        # e. tolerance_policy_id sequence
        actual_tol_ids = tuple(m.tolerance_policy_id for m in imported.valuation_result.valuation_measures)
        expected_tol_ids = tuple(m.tolerance_policy_id for m in result.valuation_measures)
        assert actual_tol_ids == expected_tol_ids

        # f. theta lineage
        if expect_theta_lineage:
            assert imported.valuation_result.theta_roll_boundary_contract_name == THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1
            assert imported.valuation_result.theta_roll_boundary_contract_version == THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1
            assert imported.valuation_result.theta_roll_boundary_reference is not None
        else:
            assert imported.valuation_result.theta_roll_boundary_contract_name is None
            assert imported.valuation_result.theta_roll_boundary_contract_version is None
            assert imported.valuation_result.theta_roll_boundary_reference is None

def test_stale_artifact_hash_is_rejected() -> None:
    result = _full_canonical_result()
    artifact = build_option_pricing_artifact_v2(valuation_result=result)
    tampered = OptionPricingArtifactV2(
        artifact_contract_name=artifact.artifact_contract_name,
        artifact_contract_version=artifact.artifact_contract_version,
        valuation_result=artifact.valuation_result,
        canonical_payload_hash="0" * 64,
    )
    with pytest.raises(ValueError, match="canonical_payload_hash"):
        export_option_pricing_artifact_payload_v2(artifact=tampered)

def test_import_rejects_semantic_synthesis() -> None:
    # Remove theta lineage from full canonical payload (should be rejected)
    result = _full_canonical_result()
    artifact = build_option_pricing_artifact_v2(valuation_result=result)
    payload = json.loads(export_option_pricing_artifact_payload_v2(artifact=artifact))
    payload["theta_roll_boundary_contract_name"] = None
    payload["theta_roll_boundary_contract_version"] = None
    payload["theta_roll_boundary_reference"] = None
    with pytest.raises(ValueError, match="required for full canonical measure set"):
        import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=json.dumps(payload, separators=(",", ":")))
    # Add theta lineage to model-direct payload (should be rejected)
    result2 = _model_direct_result()
    artifact2 = build_option_pricing_artifact_v2(valuation_result=result2)
    payload2 = json.loads(export_option_pricing_artifact_payload_v2(artifact=artifact2))
    payload2["theta_roll_boundary_contract_name"] = THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1
    payload2["theta_roll_boundary_contract_version"] = THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1
    payload2["theta_roll_boundary_reference"] = "fake"
    with pytest.raises(ValueError, match="theta boundary lineage must be None for model-direct measure set"):
        import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=json.dumps(payload2, separators=(",", ":")))

def test_no_runtime_fields_in_exported_payload() -> None:
    result = _full_canonical_result()
    artifact = build_option_pricing_artifact_v2(valuation_result=result)
    payload = export_option_pricing_artifact_payload_v2(artifact=artifact)
    forbidden = {"timestamp", "uuid", "host", "process", "file_path", "metadata"}
    for k in forbidden:
        assert k not in payload

def test_identity_constants_are_preserved() -> None:
    result = _full_canonical_result()
    artifact = build_option_pricing_artifact_v2(valuation_result=result)
    payload = export_option_pricing_artifact_payload_v2(artifact=artifact)
    imported = import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=payload)
    assert imported.artifact_contract_name == ARTIFACT_CONTRACT_NAME_V2
    assert imported.artifact_contract_version == ARTIFACT_CONTRACT_VERSION_V2
    assert imported.canonical_payload_hash == canonical_option_pricing_artifact_payload_hash_v2(valuation_result=imported.valuation_result)
    assert [f.name for f in fields(imported)] == ["artifact_contract_name", "artifact_contract_version", "valuation_result", "canonical_payload_hash"]
