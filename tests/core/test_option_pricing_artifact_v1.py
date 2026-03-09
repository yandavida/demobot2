from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from core.contracts.option_pricing_artifact_v1 import OptionPricingArtifactV1
from core.contracts.option_valuation_result_v1 import OptionValuationResultV1
from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1
from core.contracts.valuation_measure_result_v1 import ValuationMeasureResultV1
from core.contracts.valuation_measure_set_v1 import PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1


def _valuation_result() -> OptionValuationResultV1:
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


def test_artifact_contract_is_immutable() -> None:
    artifact = OptionPricingArtifactV1(
        artifact_contract_name="OptionPricingArtifactV1",
        artifact_contract_version="1.0.0",
        valuation_result=_valuation_result(),
        canonical_payload_hash="a" * 64,
    )

    with pytest.raises(FrozenInstanceError):
        artifact.canonical_payload_hash = "b" * 64


def test_artifact_requires_non_empty_identity_and_typed_valuation_result() -> None:
    with pytest.raises(ValueError, match="artifact_contract_name"):
        OptionPricingArtifactV1(
            artifact_contract_name="",
            artifact_contract_version="1.0.0",
            valuation_result=_valuation_result(),
            canonical_payload_hash="a" * 64,
        )

    with pytest.raises(ValueError, match="artifact_contract_version"):
        OptionPricingArtifactV1(
            artifact_contract_name="OptionPricingArtifactV1",
            artifact_contract_version="",
            valuation_result=_valuation_result(),
            canonical_payload_hash="a" * 64,
        )

    with pytest.raises(ValueError, match="valuation_result"):
        OptionPricingArtifactV1(
            artifact_contract_name="OptionPricingArtifactV1",
            artifact_contract_version="1.0.0",
            valuation_result="not-a-result",
            canonical_payload_hash="a" * 64,
        )


def test_artifact_rejects_malformed_hash() -> None:
    with pytest.raises(ValueError, match="canonical_payload_hash"):
        OptionPricingArtifactV1(
            artifact_contract_name="OptionPricingArtifactV1",
            artifact_contract_version="1.0.0",
            valuation_result=_valuation_result(),
            canonical_payload_hash="abc",
        )

    with pytest.raises(ValueError, match="canonical_payload_hash"):
        OptionPricingArtifactV1(
            artifact_contract_name="OptionPricingArtifactV1",
            artifact_contract_version="1.0.0",
            valuation_result=_valuation_result(),
            canonical_payload_hash="A" * 64,
        )
