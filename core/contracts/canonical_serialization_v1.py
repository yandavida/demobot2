from __future__ import annotations

from decimal import Decimal
import json

from core.contracts.option_valuation_result_v1 import OptionValuationResultV1
from core.contracts.valuation_measure_result_v1 import ValuationMeasureResultV1


def _require_non_empty_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    return value


def canonical_decimal_text_v1(value: Decimal) -> str:
    """Return canonical decimal text using plain notation and explicit trailing-zero normalization."""

    if not isinstance(value, Decimal):
        raise ValueError("value must be Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")

    if value == Decimal("0"):
        return "0"

    normalized = value.normalize()
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text == "-0":
        return "0"
    return text


def _serialize_measure_result_v1(measure: ValuationMeasureResultV1) -> dict[str, str]:
    if not isinstance(measure, ValuationMeasureResultV1):
        raise ValueError("measure must be ValuationMeasureResultV1")

    return {
        "measure_name": measure.measure_name.value,
        "value": canonical_decimal_text_v1(measure.value),
    }


def _serialize_option_valuation_result_v1(valuation_result: OptionValuationResultV1) -> dict[str, object]:
    if not isinstance(valuation_result, OptionValuationResultV1):
        raise ValueError("valuation_result must be OptionValuationResultV1")

    return {
        "engine_name": valuation_result.engine_name,
        "engine_version": valuation_result.engine_version,
        "model_name": valuation_result.model_name,
        "model_version": valuation_result.model_version,
        "resolved_input_contract_name": valuation_result.resolved_input_contract_name,
        "resolved_input_contract_version": valuation_result.resolved_input_contract_version,
        "resolved_input_reference": valuation_result.resolved_input_reference,
        "valuation_measures": [_serialize_measure_result_v1(item) for item in valuation_result.valuation_measures],
    }


def canonical_serialize_option_pricing_artifact_payload_v1(
    *,
    artifact_contract_name: str,
    artifact_contract_version: str,
    valuation_result: OptionValuationResultV1,
) -> str:
    """Serialize artifact payload deterministically using fixed field ordering and compact JSON."""

    artifact_contract_name = _require_non_empty_string(artifact_contract_name, "artifact_contract_name")
    artifact_contract_version = _require_non_empty_string(artifact_contract_version, "artifact_contract_version")

    payload = {
        "artifact_contract_name": artifact_contract_name,
        "artifact_contract_version": artifact_contract_version,
        "valuation_result": _serialize_option_valuation_result_v1(valuation_result),
    }

    return json.dumps(
        payload,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    )


__all__ = [
    "canonical_decimal_text_v1",
    "canonical_serialize_option_pricing_artifact_payload_v1",
]
