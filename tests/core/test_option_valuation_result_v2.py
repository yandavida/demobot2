from __future__ import annotations

from dataclasses import FrozenInstanceError
from dataclasses import fields
from decimal import Decimal

import pytest

from core.contracts.option_valuation_result_v1 import OptionValuationResultV1
from core.contracts.option_valuation_result_v2 import OptionValuationResultV2
from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1
from core.contracts.valuation_measure_result_v1 import ValuationMeasureResultV1
from core.contracts.valuation_measure_result_v2 import ValuationMeasureMethodKindV2
from core.contracts.valuation_measure_result_v2 import ValuationMeasureResultV2
from core.contracts.valuation_measure_set_v1 import PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1
from core.contracts.valuation_measure_set_v1 import PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1


def _v2_measure_results() -> tuple[ValuationMeasureResultV2, ...]:
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

    results: list[ValuationMeasureResultV2] = []
    for measure_name in PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1:
        if measure_name in numerical_measures:
            results.append(
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
            results.append(
                ValuationMeasureResultV2(
                    measure_name=measure_name,
                    value=values[measure_name],
                    method_kind=ValuationMeasureMethodKindV2.MODEL_DIRECT,
                    measure_policy_id="phase_d.measure_policy.v2",
                )
            )
    return tuple(results)


def _v2_result(**overrides: object) -> OptionValuationResultV2:
    payload: dict[str, object] = {
        "engine_name": "american_crr_fx_engine",
        "engine_version": "2.0.0",
        "model_name": "crr_recombining_binomial",
        "model_version": "1.0.0",
        "resolved_input_contract_name": "ResolvedFxOptionValuationInputsV1",
        "resolved_input_contract_version": "1.0.0",
        "resolved_input_reference": "resolved-input-ref-2027-01-01-run-001",
        "resolved_lattice_policy_contract_name": "ResolvedAmericanLatticePolicyV1",
        "resolved_lattice_policy_contract_version": "1.0.0",
        "resolved_lattice_policy_reference": "resolved-lattice-policy-ref-2027-01-01-run-001",
        "valuation_measures": _v2_measure_results(),
    }
    payload.update(overrides)
    return OptionValuationResultV2(**payload)


def test_v2_measure_result_fields_are_explicit_and_no_metadata_blob() -> None:
    assert [field.name for field in fields(ValuationMeasureResultV2)] == [
        "measure_name",
        "value",
        "method_kind",
        "measure_policy_id",
        "bump_policy_id",
        "tolerance_policy_id",
    ]


def test_v2_measure_and_result_contracts_are_immutable() -> None:
    measure = _v2_measure_results()[0]
    result = _v2_result()

    with pytest.raises(FrozenInstanceError):
        measure.measure_policy_id = "other"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        result.engine_name = "other"  # type: ignore[misc]


def test_v1_contract_shapes_remain_frozen() -> None:
    assert [field.name for field in fields(ValuationMeasureResultV1)] == [
        "measure_name",
        "value",
    ]
    assert [field.name for field in fields(OptionValuationResultV1)] == [
        "engine_name",
        "engine_version",
        "model_name",
        "model_version",
        "resolved_input_contract_name",
        "resolved_input_contract_version",
        "resolved_input_reference",
        "valuation_measures",
    ]


def test_minimalism_guard_no_future_phase_semantics_in_v2_shapes() -> None:
    forbidden = {"portfolio", "scenario", "basket", "lifecycle", "advisory", "metadata"}

    v2_measure_fields = {field.name for field in fields(ValuationMeasureResultV2)}
    v2_result_fields = {field.name for field in fields(OptionValuationResultV2)}

    assert v2_measure_fields.isdisjoint(forbidden)
    assert v2_result_fields.isdisjoint(forbidden)


def test_v2_measure_requires_provenance_and_policy_traceability() -> None:
    with pytest.raises(ValueError, match="method_kind"):
        ValuationMeasureResultV2(
            measure_name=ValuationMeasureNameV1.PRESENT_VALUE,
            value=Decimal("1"),
            method_kind="model_direct",  # type: ignore[arg-type]
            measure_policy_id="phase_d.measure_policy.v2",
        )

    with pytest.raises(ValueError, match="measure_policy_id"):
        ValuationMeasureResultV2(
            measure_name=ValuationMeasureNameV1.PRESENT_VALUE,
            value=Decimal("1"),
            method_kind=ValuationMeasureMethodKindV2.MODEL_DIRECT,
            measure_policy_id="",
        )


def test_numerical_method_requires_explicit_bump_and_tolerance_traceability() -> None:
    with pytest.raises(ValueError, match="bump_policy_id"):
        ValuationMeasureResultV2(
            measure_name=ValuationMeasureNameV1.DELTA_SPOT_NON_PREMIUM_ADJUSTED,
            value=Decimal("1"),
            method_kind=ValuationMeasureMethodKindV2.NUMERICAL_BUMP_REPRICE,
            measure_policy_id="phase_d.measure_policy.v2",
            tolerance_policy_id="phase_d.tolerance_policy.v1",
        )

    with pytest.raises(ValueError, match="tolerance_policy_id"):
        ValuationMeasureResultV2(
            measure_name=ValuationMeasureNameV1.DELTA_SPOT_NON_PREMIUM_ADJUSTED,
            value=Decimal("1"),
            method_kind=ValuationMeasureMethodKindV2.NUMERICAL_BUMP_REPRICE,
            measure_policy_id="phase_d.measure_policy.v2",
            bump_policy_id="phase_d.bump_policy.v1",
        )


def test_v2_result_enforces_canonical_measure_completeness_and_order() -> None:
    measures = _v2_measure_results()
    with pytest.raises(ValueError, match="approved governed measure set"):
        _v2_result(valuation_measures=measures[:-1])

    swapped = list(measures)
    swapped[0], swapped[1] = swapped[1], swapped[0]
    with pytest.raises(ValueError, match="canonical order"):
        _v2_result(valuation_measures=tuple(swapped))


def test_v2_result_accepts_governed_model_direct_slice_in_canonical_order() -> None:
    model_direct_only = tuple(
        ValuationMeasureResultV2(
            measure_name=measure_name,
            value=Decimal(index + 1),
            method_kind=ValuationMeasureMethodKindV2.MODEL_DIRECT,
            measure_policy_id="phase_d.measure_policy.v2",
        )
        for index, measure_name in enumerate(PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1)
    )

    result = _v2_result(valuation_measures=model_direct_only)

    assert tuple(item.measure_name for item in result.valuation_measures) == PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1


def test_v2_result_identity_and_lineage_shape_is_explicit() -> None:
    result = _v2_result()

    assert result.engine_name == "american_crr_fx_engine"
    assert result.engine_version == "2.0.0"
    assert result.model_name == "crr_recombining_binomial"
    assert result.model_version == "1.0.0"
    assert result.resolved_input_contract_name == "ResolvedFxOptionValuationInputsV1"
    assert result.resolved_input_contract_version == "1.0.0"
    assert result.resolved_input_reference == "resolved-input-ref-2027-01-01-run-001"
    assert result.resolved_lattice_policy_contract_name == "ResolvedAmericanLatticePolicyV1"
    assert result.resolved_lattice_policy_contract_version == "1.0.0"
    assert result.resolved_lattice_policy_reference == "resolved-lattice-policy-ref-2027-01-01-run-001"


def test_model_direct_outputs_use_model_direct_method_kind() -> None:
    measures = _v2_measure_results()

    assert measures[0].measure_name == ValuationMeasureNameV1.PRESENT_VALUE
    assert measures[0].method_kind == ValuationMeasureMethodKindV2.MODEL_DIRECT

    assert measures[1].measure_name == ValuationMeasureNameV1.INTRINSIC_VALUE
    assert measures[1].method_kind == ValuationMeasureMethodKindV2.MODEL_DIRECT

    assert measures[2].measure_name == ValuationMeasureNameV1.TIME_VALUE
    assert measures[2].method_kind == ValuationMeasureMethodKindV2.MODEL_DIRECT