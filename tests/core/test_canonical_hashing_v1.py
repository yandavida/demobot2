from __future__ import annotations

from decimal import Decimal

import pytest

from core.contracts.canonical_hashing_v1 import CANONICAL_HASH_ALGORITHM_V1
from core.contracts.canonical_hashing_v1 import canonical_hash_from_serialized_payload_v1
from core.contracts.canonical_hashing_v1 import canonical_option_pricing_artifact_hash_v1
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


def test_hash_algorithm_is_frozen() -> None:
    assert CANONICAL_HASH_ALGORITHM_V1 == "sha256"


def test_hash_is_deterministic_for_identical_payloads() -> None:
    result = _valuation_result()

    hash_1 = canonical_option_pricing_artifact_hash_v1(
        artifact_contract_name="OptionPricingArtifactV1",
        artifact_contract_version="1.0.0",
        valuation_result=result,
    )
    hash_2 = canonical_option_pricing_artifact_hash_v1(
        artifact_contract_name="OptionPricingArtifactV1",
        artifact_contract_version="1.0.0",
        valuation_result=result,
    )

    assert hash_1 == hash_2
    assert len(hash_1) == 64


def test_hash_changes_when_payload_changes() -> None:
    hash_1 = canonical_option_pricing_artifact_hash_v1(
        artifact_contract_name="OptionPricingArtifactV1",
        artifact_contract_version="1.0.0",
        valuation_result=_valuation_result(present_value=Decimal("100.00")),
    )
    hash_2 = canonical_option_pricing_artifact_hash_v1(
        artifact_contract_name="OptionPricingArtifactV1",
        artifact_contract_version="1.0.0",
        valuation_result=_valuation_result(present_value=Decimal("101.00")),
    )

    assert hash_1 != hash_2


def test_hash_from_serialized_payload_is_strictly_typed() -> None:
    with pytest.raises(ValueError, match="serialized_payload"):
        canonical_hash_from_serialized_payload_v1(123)
