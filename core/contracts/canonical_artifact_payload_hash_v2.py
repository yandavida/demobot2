from __future__ import annotations

import hashlib
import json

from core.contracts.canonical_serialization_v1 import canonical_decimal_text_v1
from core.contracts.option_valuation_result_v2 import OptionValuationResultV2
from core.contracts.valuation_measure_result_v2 import ValuationMeasureResultV2


CANONICAL_HASH_ALGORITHM_V2 = "sha256"


def _serialize_measure_v2(measure: ValuationMeasureResultV2) -> dict[str, str | None]:
    if not isinstance(measure, ValuationMeasureResultV2):
        raise ValueError("measure must be ValuationMeasureResultV2")

    return {
        "measure_name": measure.measure_name.value,
        "value": canonical_decimal_text_v1(measure.value),
        "method_kind": measure.method_kind.value,
        "measure_policy_id": measure.measure_policy_id,
        "bump_policy_id": measure.bump_policy_id,
        "tolerance_policy_id": measure.tolerance_policy_id,
    }


def canonical_option_pricing_artifact_payload_v2(
    *,
    valuation_result: OptionValuationResultV2,
) -> dict[str, object]:
    """Derive deterministic governed canonical payload for OptionPricingArtifactV2 foundation."""

    if not isinstance(valuation_result, OptionValuationResultV2):
        raise ValueError("valuation_result must be OptionValuationResultV2")

    return {
        "engine_name": valuation_result.engine_name,
        "engine_version": valuation_result.engine_version,
        "model_name": valuation_result.model_name,
        "model_version": valuation_result.model_version,
        "resolved_input_contract_name": valuation_result.resolved_input_contract_name,
        "resolved_input_contract_version": valuation_result.resolved_input_contract_version,
        "resolved_input_reference": valuation_result.resolved_input_reference,
        "resolved_lattice_policy_contract_name": valuation_result.resolved_lattice_policy_contract_name,
        "resolved_lattice_policy_contract_version": valuation_result.resolved_lattice_policy_contract_version,
        "resolved_lattice_policy_reference": valuation_result.resolved_lattice_policy_reference,
        "theta_roll_boundary_contract_name": valuation_result.theta_roll_boundary_contract_name,
        "theta_roll_boundary_contract_version": valuation_result.theta_roll_boundary_contract_version,
        "theta_roll_boundary_reference": valuation_result.theta_roll_boundary_reference,
        "valuation_measures": [_serialize_measure_v2(item) for item in valuation_result.valuation_measures],
    }


def canonical_serialize_option_pricing_artifact_payload_v2(
    *,
    valuation_result: OptionValuationResultV2,
) -> str:
    """Serialize canonical payload deterministically with compact JSON and fixed field order."""

    payload = canonical_option_pricing_artifact_payload_v2(valuation_result=valuation_result)
    return json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    )


def canonical_option_pricing_artifact_payload_hash_v2(
    *,
    valuation_result: OptionValuationResultV2,
) -> str:
    """Compute lowercase SHA-256 hex digest from canonical serialized payload."""

    if CANONICAL_HASH_ALGORITHM_V2 != "sha256":
        raise ValueError("unsupported canonical hash algorithm")

    serialized_payload = canonical_serialize_option_pricing_artifact_payload_v2(
        valuation_result=valuation_result,
    )
    return hashlib.sha256(serialized_payload.encode("utf-8")).hexdigest()


__all__ = [
    "CANONICAL_HASH_ALGORITHM_V2",
    "canonical_option_pricing_artifact_payload_v2",
    "canonical_serialize_option_pricing_artifact_payload_v2",
    "canonical_option_pricing_artifact_payload_hash_v2",
]
