from __future__ import annotations

from dataclasses import FrozenInstanceError
from dataclasses import fields
from decimal import Decimal

import pytest

from core.contracts.option_valuation_result_v1 import OptionValuationResultV1
from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1
from core.contracts.valuation_measure_result_v1 import ValuationMeasureResultV1
from core.contracts.valuation_measure_set_v1 import PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1


def _measure_results() -> tuple[ValuationMeasureResultV1, ...]:
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
    return tuple(
        ValuationMeasureResultV1(measure_name=measure_name, value=values[measure_name])
        for measure_name in PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1
    )


def _result(**overrides: object) -> OptionValuationResultV1:
    payload: dict[str, object] = {
        "engine_name": "black_scholes_european_fx_engine",
        "engine_version": "1.0.0",
        "model_name": "garman_kohlhagen",
        "model_version": "1.0.0",
        "resolved_input_contract_name": "ResolvedFxOptionValuationInputsV1",
        "resolved_input_contract_version": "1.0.0",
        "resolved_input_reference": "resolved-input-ref-2026-12-31-run-001",
        "valuation_measures": _measure_results(),
    }
    payload.update(overrides)
    return OptionValuationResultV1(**payload)


def test_contract_fields_are_stable_and_required() -> None:
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


def test_constructs_with_explicit_valid_values() -> None:
    result = _result()

    assert result.engine_name == "black_scholes_european_fx_engine"
    assert result.model_name == "garman_kohlhagen"
    assert tuple(measure.measure_name for measure in result.valuation_measures) == PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1


def test_contract_is_immutable() -> None:
    result = _result()

    with pytest.raises(FrozenInstanceError):
        result.engine_name = "other"


def test_rejects_empty_engine_or_model_identity_fields() -> None:
    with pytest.raises(ValueError, match="engine_name"):
        _result(engine_name="")

    with pytest.raises(ValueError, match="engine_version"):
        _result(engine_version="")

    with pytest.raises(ValueError, match="model_name"):
        _result(model_name="")

    with pytest.raises(ValueError, match="model_version"):
        _result(model_version="")


def test_rejects_empty_lineage_fields() -> None:
    with pytest.raises(ValueError, match="resolved_input_contract_name"):
        _result(resolved_input_contract_name="")

    with pytest.raises(ValueError, match="resolved_input_contract_version"):
        _result(resolved_input_contract_version="")

    with pytest.raises(ValueError, match="resolved_input_reference"):
        _result(resolved_input_reference="")


def test_rejects_non_tuple_measure_collection() -> None:
    with pytest.raises(ValueError, match="valuation_measures must be a tuple"):
        _result(valuation_measures=list(_measure_results()))


def test_rejects_non_contract_measure_entries() -> None:
    malformed = tuple(_measure_results()[:-1]) + ({"measure_name": "present_value", "value": "1"},)

    with pytest.raises(ValueError, match="valuation_measures entries must be ValuationMeasureResultV1"):
        _result(valuation_measures=malformed)


def test_rejects_missing_approved_measure() -> None:
    with pytest.raises(ValueError, match="exactly the approved Phase C measure set"):
        _result(valuation_measures=_measure_results()[:-1])


def test_rejects_duplicate_or_extra_measures() -> None:
    duplicated = _measure_results() + (_measure_results()[0],)

    with pytest.raises(ValueError, match="exactly the approved Phase C measure set"):
        _result(valuation_measures=duplicated)


def test_rejects_wrong_measure_order() -> None:
    measures = list(_measure_results())
    measures[0], measures[1] = measures[1], measures[0]

    with pytest.raises(ValueError, match="canonical order"):
        _result(valuation_measures=tuple(measures))


def test_requires_explicit_arguments_and_no_hidden_defaults() -> None:
    with pytest.raises(TypeError):
        OptionValuationResultV1()  # type: ignore[call-arg]
