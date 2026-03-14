from __future__ import annotations

from decimal import Decimal

from core.contracts.canonical_artifact_payload_hash_v2 import CANONICAL_HASH_ALGORITHM_V2
from core.contracts.canonical_artifact_payload_hash_v2 import canonical_option_pricing_artifact_payload_hash_v2
from core.contracts.canonical_artifact_payload_hash_v2 import canonical_option_pricing_artifact_payload_v2
from core.contracts.canonical_artifact_payload_hash_v2 import canonical_serialize_option_pricing_artifact_payload_v2
from core.contracts.option_valuation_result_v2 import OptionValuationResultV2
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1
from core.contracts.theta_rolled_fx_inputs_boundary_v1 import THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1
from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1
from core.contracts.valuation_measure_result_v2 import ValuationMeasureMethodKindV2
from core.contracts.valuation_measure_result_v2 import ValuationMeasureResultV2
from core.contracts.valuation_measure_set_v1 import PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1
from core.contracts.valuation_measure_set_v1 import PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1


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


def test_payload_is_deterministic_for_identical_input() -> None:
    result = _full_canonical_result()
    payload_1 = canonical_option_pricing_artifact_payload_v2(valuation_result=result)
    payload_2 = canonical_option_pricing_artifact_payload_v2(valuation_result=result)

    assert payload_1 == payload_2


def test_serialization_is_deterministic_for_identical_input() -> None:
    result = _full_canonical_result()
    serialized_1 = canonical_serialize_option_pricing_artifact_payload_v2(valuation_result=result)
    serialized_2 = canonical_serialize_option_pricing_artifact_payload_v2(valuation_result=result)

    assert serialized_1 == serialized_2


def test_serialization_preserves_non_ascii_without_escaping() -> None:
    base = _model_direct_result()
    result = OptionValuationResultV2(**({**base.__dict__, "engine_name": "american_crr_fx_engine_א"}))

    serialized = canonical_serialize_option_pricing_artifact_payload_v2(valuation_result=result)

    assert "american_crr_fx_engine_א" in serialized
    assert "\\u05d0" not in serialized


def test_hash_is_deterministic_for_identical_input() -> None:
    result = _full_canonical_result()
    hash_1 = canonical_option_pricing_artifact_payload_hash_v2(valuation_result=result)
    hash_2 = canonical_option_pricing_artifact_payload_hash_v2(valuation_result=result)

    assert hash_1 == hash_2


def test_full_canonical_payload_includes_theta_boundary_lineage() -> None:
    payload = canonical_option_pricing_artifact_payload_v2(valuation_result=_full_canonical_result())

    assert payload["theta_roll_boundary_contract_name"] == THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_NAME_V1
    assert payload["theta_roll_boundary_contract_version"] == THETA_ROLLED_INPUT_BOUNDARY_CONTRACT_VERSION_V1
    assert payload["theta_roll_boundary_reference"] == (
        "ThetaRolledFxInputsBoundaryV1:"
        "current_resolved_input_reference=sha256:current;"
        "theta_rolled_resolved_input_reference=sha256:rolled;"
        "theta_roll_policy_id=theta_rolled_resolved_input_1d_calendar_upstream_v1"
    )


def test_model_direct_slice_preserves_no_theta_lineage_semantics() -> None:
    payload = canonical_option_pricing_artifact_payload_v2(valuation_result=_model_direct_result())

    assert payload["theta_roll_boundary_contract_name"] is None
    assert payload["theta_roll_boundary_contract_version"] is None
    assert payload["theta_roll_boundary_reference"] is None


def test_canonical_measure_order_is_preserved_exactly() -> None:
    payload = canonical_option_pricing_artifact_payload_v2(valuation_result=_full_canonical_result())
    measure_names = tuple(item["measure_name"] for item in payload["valuation_measures"])

    assert measure_names == tuple(item.value for item in PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1)


def test_hash_format_is_lowercase_64_char_hex() -> None:
    digest = canonical_option_pricing_artifact_payload_hash_v2(valuation_result=_full_canonical_result())

    assert len(digest) == 64
    assert digest == digest.lower()
    assert all(char in "0123456789abcdef" for char in digest)


def test_no_forbidden_runtime_fields_appear_in_payload() -> None:
    payload = canonical_option_pricing_artifact_payload_v2(valuation_result=_full_canonical_result())
    serialized = canonical_serialize_option_pricing_artifact_payload_v2(valuation_result=_full_canonical_result())

    forbidden = {
        "timestamp",
        "uuid",
        "host",
        "process",
        "file_path",
        "metadata",
    }

    assert forbidden.isdisjoint(set(payload.keys()))
    for item in forbidden:
        assert item not in serialized


def test_equal_semantic_inputs_produce_equal_hashes() -> None:
    hash_1 = canonical_option_pricing_artifact_payload_hash_v2(valuation_result=_full_canonical_result())
    hash_2 = canonical_option_pricing_artifact_payload_hash_v2(valuation_result=_full_canonical_result())

    assert hash_1 == hash_2


def test_load_bearing_field_mutations_change_hash_and_do_not_collide() -> None:
    baseline = _full_canonical_result()
    baseline_hash = canonical_option_pricing_artifact_payload_hash_v2(valuation_result=baseline)

    mutation_hashes = []

    mutated_resolved_input = OptionValuationResultV2(
        **({**baseline.__dict__, "resolved_input_reference": "sha256:resolved-other"})
    )
    mutation_hashes.append(canonical_option_pricing_artifact_payload_hash_v2(valuation_result=mutated_resolved_input))

    mutated_lattice = OptionValuationResultV2(
        **({**baseline.__dict__, "resolved_lattice_policy_reference": "ResolvedAmericanLatticePolicyV1:model_family_id=american_crr_recombining_binomial_v1;step_count=251;early_exercise_policy_id=american_early_exercise_max_with_intrinsic_floor_v1;convergence_policy_id=american_crr_step_convergence_pr_d_v1;edge_case_policy_id=american_crr_edge_cases_intrinsic_floor_v1;bump_policy_id=american_crr_bump_reprice_policy_pr_d_v1;tolerance_policy_id=american_crr_numerical_tolerance_policy_pr_d_v1"})
    )
    mutation_hashes.append(canonical_option_pricing_artifact_payload_hash_v2(valuation_result=mutated_lattice))

    mutated_theta_reference = OptionValuationResultV2(
        **({**baseline.__dict__, "theta_roll_boundary_reference": "ThetaRolledFxInputsBoundaryV1:current_resolved_input_reference=sha256:currentX;theta_rolled_resolved_input_reference=sha256:rolled;theta_roll_policy_id=theta_rolled_resolved_input_1d_calendar_upstream_v1"})
    )
    mutation_hashes.append(canonical_option_pricing_artifact_payload_hash_v2(valuation_result=mutated_theta_reference))

    measures_value = list(baseline.valuation_measures)
    measures_value[0] = ValuationMeasureResultV2(
        measure_name=measures_value[0].measure_name,
        value=Decimal("100.01"),
        method_kind=measures_value[0].method_kind,
        measure_policy_id=measures_value[0].measure_policy_id,
        bump_policy_id=measures_value[0].bump_policy_id,
        tolerance_policy_id=measures_value[0].tolerance_policy_id,
    )
    mutated_measure_value = OptionValuationResultV2(**({**baseline.__dict__, "valuation_measures": tuple(measures_value)}))
    mutation_hashes.append(canonical_option_pricing_artifact_payload_hash_v2(valuation_result=mutated_measure_value))

    measures_method = list(baseline.valuation_measures)
    measures_method[3] = ValuationMeasureResultV2(
        measure_name=measures_method[3].measure_name,
        value=measures_method[3].value,
        method_kind=ValuationMeasureMethodKindV2.MODEL_DIRECT,
        measure_policy_id=measures_method[3].measure_policy_id,
        bump_policy_id=measures_method[3].bump_policy_id,
        tolerance_policy_id=measures_method[3].tolerance_policy_id,
    )
    mutated_method_kind = OptionValuationResultV2(**({**baseline.__dict__, "valuation_measures": tuple(measures_method)}))
    mutation_hashes.append(canonical_option_pricing_artifact_payload_hash_v2(valuation_result=mutated_method_kind))

    measures_policy = list(baseline.valuation_measures)
    measures_policy[3] = ValuationMeasureResultV2(
        measure_name=measures_policy[3].measure_name,
        value=measures_policy[3].value,
        method_kind=measures_policy[3].method_kind,
        measure_policy_id="phase_d.measure_policy.other.v1",
        bump_policy_id=measures_policy[3].bump_policy_id,
        tolerance_policy_id=measures_policy[3].tolerance_policy_id,
    )
    mutated_measure_policy = OptionValuationResultV2(**({**baseline.__dict__, "valuation_measures": tuple(measures_policy)}))
    mutation_hashes.append(canonical_option_pricing_artifact_payload_hash_v2(valuation_result=mutated_measure_policy))

    measures_bump = list(baseline.valuation_measures)
    measures_bump[3] = ValuationMeasureResultV2(
        measure_name=measures_bump[3].measure_name,
        value=measures_bump[3].value,
        method_kind=measures_bump[3].method_kind,
        measure_policy_id=measures_bump[3].measure_policy_id,
        bump_policy_id="phase_d.bump_policy.other.v1",
        tolerance_policy_id=measures_bump[3].tolerance_policy_id,
    )
    mutated_bump_policy = OptionValuationResultV2(**({**baseline.__dict__, "valuation_measures": tuple(measures_bump)}))
    mutation_hashes.append(canonical_option_pricing_artifact_payload_hash_v2(valuation_result=mutated_bump_policy))

    measures_tolerance = list(baseline.valuation_measures)
    measures_tolerance[3] = ValuationMeasureResultV2(
        measure_name=measures_tolerance[3].measure_name,
        value=measures_tolerance[3].value,
        method_kind=measures_tolerance[3].method_kind,
        measure_policy_id=measures_tolerance[3].measure_policy_id,
        bump_policy_id=measures_tolerance[3].bump_policy_id,
        tolerance_policy_id="phase_d.tolerance_policy.other.v1",
    )
    mutated_tolerance_policy = OptionValuationResultV2(**({**baseline.__dict__, "valuation_measures": tuple(measures_tolerance)}))
    mutation_hashes.append(canonical_option_pricing_artifact_payload_hash_v2(valuation_result=mutated_tolerance_policy))

    assert all(item != baseline_hash for item in mutation_hashes)
    assert len(set(mutation_hashes)) == len(mutation_hashes)


def test_payload_and_hash_generation_are_pure_and_do_not_mutate_source() -> None:
    result = _full_canonical_result()
    before = result

    payload = canonical_option_pricing_artifact_payload_v2(valuation_result=result)
    serialized = canonical_serialize_option_pricing_artifact_payload_v2(valuation_result=result)
    digest = canonical_option_pricing_artifact_payload_hash_v2(valuation_result=result)

    assert before == result
    assert payload["engine_name"] == result.engine_name
    assert isinstance(serialized, str)
    assert isinstance(digest, str)


def test_hash_algorithm_constant_is_frozen() -> None:
    assert CANONICAL_HASH_ALGORITHM_V2 == "sha256"
