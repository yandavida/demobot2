from __future__ import annotations

from decimal import Decimal
import inspect

import pytest

from core.contracts.canonical_hashing_v1 import canonical_option_pricing_artifact_hash_v1
from core.contracts.option_pricing_artifact_v1 import OptionPricingArtifactV1
from core.contracts.option_valuation_result_v1 import OptionValuationResultV1
from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1
from core.contracts.valuation_measure_result_v1 import ValuationMeasureResultV1
from core.contracts.valuation_measure_set_v1 import PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1
from core.services.pricing_artifact_builder_v1 import ARTIFACT_CONTRACT_NAME_V1
from core.services.pricing_artifact_builder_v1 import ARTIFACT_CONTRACT_VERSION_V1
from core.services.pricing_artifact_builder_v1 import build_option_pricing_artifact_v1
from core.services.pricing_artifact_builder_v1 import __name__ as builder_module_name


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


def test_builder_emits_artifact_contract_type() -> None:
    artifact = build_option_pricing_artifact_v1(
        valuation_result=_valuation_result(),
    )

    assert isinstance(artifact, OptionPricingArtifactV1)


def test_builder_is_deterministic_for_identical_inputs() -> None:
    valuation_result = _valuation_result()

    artifact_1 = build_option_pricing_artifact_v1(
        valuation_result=valuation_result,
    )
    artifact_2 = build_option_pricing_artifact_v1(
        valuation_result=valuation_result,
    )

    assert artifact_1 == artifact_2
    assert artifact_1.canonical_payload_hash == artifact_2.canonical_payload_hash


def test_builder_does_not_mutate_inputs_and_does_not_invent_values() -> None:
    valuation_result = _valuation_result()

    artifact = build_option_pricing_artifact_v1(
        valuation_result=valuation_result,
    )

    assert artifact.valuation_result is valuation_result
    assert artifact.artifact_contract_name == ARTIFACT_CONTRACT_NAME_V1
    assert artifact.artifact_contract_version == ARTIFACT_CONTRACT_VERSION_V1


def test_builder_hash_changes_for_changed_payload() -> None:
    artifact_1 = build_option_pricing_artifact_v1(
        valuation_result=_valuation_result(present_value=Decimal("100.00")),
    )
    artifact_2 = build_option_pricing_artifact_v1(
        valuation_result=_valuation_result(present_value=Decimal("101.00")),
    )

    assert artifact_1.canonical_payload_hash != artifact_2.canonical_payload_hash


def test_builder_hash_matches_independent_canonical_hash_computation() -> None:
    valuation_result = _valuation_result()

    artifact = build_option_pricing_artifact_v1(
        valuation_result=valuation_result,
    )

    expected_hash = canonical_option_pricing_artifact_hash_v1(
        artifact_contract_name=ARTIFACT_CONTRACT_NAME_V1,
        artifact_contract_version=ARTIFACT_CONTRACT_VERSION_V1,
        valuation_result=valuation_result,
    )

    assert artifact.canonical_payload_hash == expected_hash


def test_builder_rejects_non_contract_input_type() -> None:
    with pytest.raises(ValueError, match="OptionValuationResultV1"):
        build_option_pricing_artifact_v1(valuation_result={})  # type: ignore[arg-type]


def test_builder_has_frozen_identity_constants() -> None:
    assert ARTIFACT_CONTRACT_NAME_V1 == "OptionPricingArtifactV1"
    assert ARTIFACT_CONTRACT_VERSION_V1 == "1.0.0"


def test_builder_module_has_no_engine_or_resolver_or_repository_imports() -> None:
    module = __import__(builder_module_name, fromlist=["*"])
    source = inspect.getsource(module)

    assert "core.persistence" not in source
    assert "option_valuation_input_resolver_v1" not in source
    assert "black_scholes" not in source
    assert "random" not in source
    assert "datetime" not in source
