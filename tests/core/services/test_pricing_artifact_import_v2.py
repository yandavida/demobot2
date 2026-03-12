from __future__ import annotations

import inspect
import json
from decimal import Decimal

import pytest

from core.contracts.canonical_artifact_payload_hash_v2 import canonical_option_pricing_artifact_payload_hash_v2
from core.contracts.option_pricing_artifact_v2 import ARTIFACT_CONTRACT_NAME_V2
from core.contracts.option_pricing_artifact_v2 import ARTIFACT_CONTRACT_VERSION_V2
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
from core.services.pricing_artifact_import_v2 import __name__ as import_module_name
from core.services.pricing_artifact_import_v2 import import_option_pricing_artifact_v2_from_canonical_payload


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


def test_successful_import_from_valid_full_canonical_exported_payload() -> None:
    source_artifact = build_option_pricing_artifact_v2(valuation_result=_full_canonical_result())
    payload = export_option_pricing_artifact_payload_v2(artifact=source_artifact)

    imported = import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=payload)

    assert imported.valuation_result == source_artifact.valuation_result


def test_successful_import_from_valid_model_direct_exported_payload() -> None:
    source_artifact = build_option_pricing_artifact_v2(valuation_result=_model_direct_result())
    payload = export_option_pricing_artifact_payload_v2(artifact=source_artifact)

    imported = import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=payload)

    assert imported.valuation_result == source_artifact.valuation_result


def test_imported_artifact_has_exact_v2_identity_constants() -> None:
    payload = export_option_pricing_artifact_payload_v2(
        artifact=build_option_pricing_artifact_v2(valuation_result=_full_canonical_result()),
    )
    imported = import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=payload)

    assert imported.artifact_contract_name == ARTIFACT_CONTRACT_NAME_V2
    assert imported.artifact_contract_version == ARTIFACT_CONTRACT_VERSION_V2


def test_imported_artifact_hash_equals_direct_recomputation() -> None:
    payload = export_option_pricing_artifact_payload_v2(
        artifact=build_option_pricing_artifact_v2(valuation_result=_full_canonical_result()),
    )
    imported = import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=payload)

    expected = canonical_option_pricing_artifact_payload_hash_v2(
        valuation_result=imported.valuation_result,
    )
    assert imported.canonical_payload_hash == expected


def test_import_export_roundtrip_is_byte_identical_for_full_canonical_payload() -> None:
    source_payload = export_option_pricing_artifact_payload_v2(
        artifact=build_option_pricing_artifact_v2(valuation_result=_full_canonical_result()),
    )

    imported = import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=source_payload)
    roundtrip_payload = export_option_pricing_artifact_payload_v2(artifact=imported)

    assert roundtrip_payload == source_payload


def test_import_export_roundtrip_is_byte_identical_for_model_direct_payload() -> None:
    source_payload = export_option_pricing_artifact_payload_v2(
        artifact=build_option_pricing_artifact_v2(valuation_result=_model_direct_result()),
    )

    imported = import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=source_payload)
    roundtrip_payload = export_option_pricing_artifact_payload_v2(artifact=imported)

    assert roundtrip_payload == source_payload


def test_malformed_json_is_rejected() -> None:
    with pytest.raises(ValueError, match="valid JSON"):
        import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload="{")


def test_wrong_top_level_type_is_rejected() -> None:
    with pytest.raises(ValueError, match="top-level JSON must be an object"):
        import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload='["x"]')


def test_missing_required_top_level_field_is_rejected() -> None:
    payload = json.loads(
        export_option_pricing_artifact_payload_v2(
            artifact=build_option_pricing_artifact_v2(valuation_result=_full_canonical_result()),
        )
    )
    payload.pop("model_version")

    with pytest.raises(ValueError, match="missing keys"):
        import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=json.dumps(payload, separators=(",", ":")))


def test_unexpected_extra_top_level_field_is_rejected() -> None:
    payload = json.loads(
        export_option_pricing_artifact_payload_v2(
            artifact=build_option_pricing_artifact_v2(valuation_result=_full_canonical_result()),
        )
    )
    payload["extra"] = "not-allowed"

    with pytest.raises(ValueError, match="unexpected keys"):
        import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=json.dumps(payload, separators=(",", ":")))


def test_malformed_measure_entry_is_rejected() -> None:
    payload = json.loads(
        export_option_pricing_artifact_payload_v2(
            artifact=build_option_pricing_artifact_v2(valuation_result=_full_canonical_result()),
        )
    )
    payload["valuation_measures"][0].pop("measure_policy_id")

    with pytest.raises(ValueError, match="missing keys"):
        import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=json.dumps(payload, separators=(",", ":")))


def test_invalid_measure_name_is_rejected() -> None:
    payload = json.loads(
        export_option_pricing_artifact_payload_v2(
            artifact=build_option_pricing_artifact_v2(valuation_result=_full_canonical_result()),
        )
    )
    payload["valuation_measures"][0]["measure_name"] = "not_a_measure"

    with pytest.raises(ValueError, match="measure_name is invalid"):
        import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=json.dumps(payload, separators=(",", ":")))


def test_invalid_method_kind_is_rejected() -> None:
    payload = json.loads(
        export_option_pricing_artifact_payload_v2(
            artifact=build_option_pricing_artifact_v2(valuation_result=_full_canonical_result()),
        )
    )
    payload["valuation_measures"][0]["method_kind"] = "not_a_method"

    with pytest.raises(ValueError, match="method_kind is invalid"):
        import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=json.dumps(payload, separators=(",", ":")))


def test_invalid_decimal_text_is_rejected() -> None:
    payload = json.loads(
        export_option_pricing_artifact_payload_v2(
            artifact=build_option_pricing_artifact_v2(valuation_result=_full_canonical_result()),
        )
    )
    payload["valuation_measures"][0]["value"] = "1.2.3"

    with pytest.raises(ValueError, match="valid decimal string"):
        import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=json.dumps(payload, separators=(",", ":")))


def test_theta_lineage_inconsistency_is_rejected_by_governed_contracts() -> None:
    payload = json.loads(
        export_option_pricing_artifact_payload_v2(
            artifact=build_option_pricing_artifact_v2(valuation_result=_full_canonical_result()),
        )
    )
    payload["theta_roll_boundary_contract_name"] = None
    payload["theta_roll_boundary_contract_version"] = None
    payload["theta_roll_boundary_reference"] = None

    with pytest.raises(ValueError, match="required for full canonical measure set"):
        import_option_pricing_artifact_v2_from_canonical_payload(canonical_payload=json.dumps(payload, separators=(",", ":")))


def test_import_module_has_no_hidden_file_io_runtime_resolver_engine_or_persistence_imports() -> None:
    module = __import__(import_module_name, fromlist=["*"])
    source = inspect.getsource(module)

    assert "open(" not in source
    assert "pathlib" not in source
    assert "os." not in source
    assert "datetime" not in source
    assert "uuid" not in source
    assert "option_valuation_input_resolver_v1" not in source
    assert "AmericanCrrFxEngineV1" not in source
    assert "crr_american_fx_kernel_v1" not in source
    assert "core.persistence" not in source
    assert "api." not in source
    assert "router" not in source
    assert "requests" not in source
