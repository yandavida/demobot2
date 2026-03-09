from __future__ import annotations

from decimal import Decimal

import pytest

from core.contracts.canonical_serialization_v1 import canonical_decimal_text_v1
from core.contracts.canonical_serialization_v1 import canonical_serialize_option_pricing_artifact_payload_v1
from core.contracts.option_valuation_result_v1 import OptionValuationResultV1
from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1
from core.contracts.valuation_measure_result_v1 import ValuationMeasureResultV1
from core.contracts.valuation_measure_set_v1 import PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1


def _valuation_result(*, present_value: Decimal = Decimal("100.00")) -> OptionValuationResultV1:
    values: dict[ValuationMeasureNameV1, Decimal] = {
        ValuationMeasureNameV1.PRESENT_VALUE: present_value,
        ValuationMeasureNameV1.INTRINSIC_VALUE: Decimal("10.00"),
        ValuationMeasureNameV1.TIME_VALUE: Decimal("90.00"),
        ValuationMeasureNameV1.DELTA_SPOT_NON_PREMIUM_ADJUSTED: Decimal("0.45"),
        ValuationMeasureNameV1.GAMMA_SPOT: Decimal("0.02"),
        ValuationMeasureNameV1.VEGA_1VOL_ABS: Decimal("1.25"),
        ValuationMeasureNameV1.THETA_1D_CALENDAR: Decimal("-0.15"),
        ValuationMeasureNameV1.RHO_DOMESTIC_1PCT: Decimal("0.80"),
        ValuationMeasureNameV1.RHO_FOREIGN_1PCT: Decimal("-0.75"),
    }
    measures = tuple(
        ValuationMeasureResultV1(measure_name=measure_name, value=values[measure_name])
        for measure_name in PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1
    )

    return OptionValuationResultV1(
        engine_name="black_scholes_european_fx_engine",
        engine_version="1.0.0",
        model_name="garman_kohlhagen",
        model_version="1.0.0",
        resolved_input_contract_name="ResolvedFxOptionValuationInputsV1",
        resolved_input_contract_version="1.0.0",
        resolved_input_reference="resolved-input-ref-2026-12-31-run-001",
        valuation_measures=measures,
    )


def test_decimal_text_is_canonical_and_stable() -> None:
    assert canonical_decimal_text_v1(Decimal("100.00")) == "100"
    assert canonical_decimal_text_v1(Decimal("0.000")) == "0"
    assert canonical_decimal_text_v1(Decimal("1.2300")) == "1.23"
    assert canonical_decimal_text_v1(Decimal("1E+3")) == "1000"
    assert canonical_decimal_text_v1(Decimal("-0.0000")) == "0"


def test_serialization_is_deterministic_for_identical_inputs() -> None:
    result = _valuation_result()

    serialized_1 = canonical_serialize_option_pricing_artifact_payload_v1(
        artifact_contract_name="OptionPricingArtifactV1",
        artifact_contract_version="1.0.0",
        valuation_result=result,
    )
    serialized_2 = canonical_serialize_option_pricing_artifact_payload_v1(
        artifact_contract_name="OptionPricingArtifactV1",
        artifact_contract_version="1.0.0",
        valuation_result=result,
    )

    assert serialized_1 == serialized_2


def test_serialization_changes_when_payload_changes() -> None:
    baseline = canonical_serialize_option_pricing_artifact_payload_v1(
        artifact_contract_name="OptionPricingArtifactV1",
        artifact_contract_version="1.0.0",
        valuation_result=_valuation_result(present_value=Decimal("100.00")),
    )
    changed = canonical_serialize_option_pricing_artifact_payload_v1(
        artifact_contract_name="OptionPricingArtifactV1",
        artifact_contract_version="1.0.0",
        valuation_result=_valuation_result(present_value=Decimal("101.00")),
    )

    assert baseline != changed


def test_serialization_preserves_measure_order() -> None:
    serialized = canonical_serialize_option_pricing_artifact_payload_v1(
        artifact_contract_name="OptionPricingArtifactV1",
        artifact_contract_version="1.0.0",
        valuation_result=_valuation_result(),
    )

    assert serialized.find('"measure_name":"present_value"') < serialized.find('"measure_name":"intrinsic_value"')
    assert serialized.find('"measure_name":"theta_1d_calendar"') < serialized.find('"measure_name":"rho_domestic_1pct"')


def test_serialization_rejects_unsupported_inputs() -> None:
    with pytest.raises(ValueError, match="artifact_contract_name"):
        canonical_serialize_option_pricing_artifact_payload_v1(
            artifact_contract_name="",
            artifact_contract_version="1.0.0",
            valuation_result=_valuation_result(),
        )

    with pytest.raises(ValueError, match="artifact_contract_version"):
        canonical_serialize_option_pricing_artifact_payload_v1(
            artifact_contract_name="OptionPricingArtifactV1",
            artifact_contract_version="",
            valuation_result=_valuation_result(),
        )

    with pytest.raises(ValueError, match="artifact_contract_name"):
        canonical_serialize_option_pricing_artifact_payload_v1(
            artifact_contract_name=" OptionPricingArtifactV1 ",
            artifact_contract_version="1.0.0",
            valuation_result=_valuation_result(),
        )

    with pytest.raises(ValueError, match="valuation_result"):
        canonical_serialize_option_pricing_artifact_payload_v1(
            artifact_contract_name="OptionPricingArtifactV1",
            artifact_contract_version="1.0.0",
            valuation_result="not-a-result",
        )

    with pytest.raises(ValueError, match="value must be Decimal"):
        canonical_decimal_text_v1("1.0")
