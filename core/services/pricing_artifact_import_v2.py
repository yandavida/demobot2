from __future__ import annotations

import json
from decimal import Decimal
from decimal import InvalidOperation

from core.contracts.canonical_artifact_payload_hash_v2 import canonical_option_pricing_artifact_payload_hash_v2
from core.contracts.option_pricing_artifact_v2 import ARTIFACT_CONTRACT_NAME_V2
from core.contracts.option_pricing_artifact_v2 import ARTIFACT_CONTRACT_VERSION_V2
from core.contracts.option_pricing_artifact_v2 import OptionPricingArtifactV2
from core.contracts.option_valuation_result_v2 import OptionValuationResultV2
from core.contracts.valuation_measure_name_v1 import ValuationMeasureNameV1
from core.contracts.valuation_measure_result_v2 import ValuationMeasureMethodKindV2
from core.contracts.valuation_measure_result_v2 import ValuationMeasureResultV2


_REQUIRED_TOP_LEVEL_KEYS_V2 = {
    "engine_name",
    "engine_version",
    "model_name",
    "model_version",
    "resolved_input_contract_name",
    "resolved_input_contract_version",
    "resolved_input_reference",
    "resolved_lattice_policy_contract_name",
    "resolved_lattice_policy_contract_version",
    "resolved_lattice_policy_reference",
    "theta_roll_boundary_contract_name",
    "theta_roll_boundary_contract_version",
    "theta_roll_boundary_reference",
    "valuation_measures",
}

_REQUIRED_MEASURE_KEYS_V2 = {
    "measure_name",
    "value",
    "method_kind",
    "measure_policy_id",
    "bump_policy_id",
    "tolerance_policy_id",
}


def _require_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    return value


def _parse_measure_v2(payload: object, index: int) -> ValuationMeasureResultV2:
    if not isinstance(payload, dict):
        raise ValueError(f"valuation_measures[{index}] must be an object")

    keys = set(payload.keys())
    missing = _REQUIRED_MEASURE_KEYS_V2 - keys
    extra = keys - _REQUIRED_MEASURE_KEYS_V2
    if missing:
        raise ValueError(f"valuation_measures[{index}] missing keys: {sorted(missing)}")
    if extra:
        raise ValueError(f"valuation_measures[{index}] has unexpected keys: {sorted(extra)}")

    measure_name_text = _require_string(payload["measure_name"], f"valuation_measures[{index}].measure_name")
    method_kind_text = _require_string(payload["method_kind"], f"valuation_measures[{index}].method_kind")
    measure_policy_id = _require_string(payload["measure_policy_id"], f"valuation_measures[{index}].measure_policy_id")

    bump_policy_id = payload["bump_policy_id"]
    if bump_policy_id is not None and not isinstance(bump_policy_id, str):
        raise ValueError(f"valuation_measures[{index}].bump_policy_id must be string or None")

    tolerance_policy_id = payload["tolerance_policy_id"]
    if tolerance_policy_id is not None and not isinstance(tolerance_policy_id, str):
        raise ValueError(f"valuation_measures[{index}].tolerance_policy_id must be string or None")

    value_text = payload["value"]
    if not isinstance(value_text, str):
        raise ValueError(f"valuation_measures[{index}].value must be string")

    try:
        value_decimal = Decimal(value_text)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"valuation_measures[{index}].value must be a valid decimal string") from exc

    try:
        measure_name = ValuationMeasureNameV1(measure_name_text)
    except ValueError as exc:
        raise ValueError(f"valuation_measures[{index}].measure_name is invalid") from exc

    try:
        method_kind = ValuationMeasureMethodKindV2(method_kind_text)
    except ValueError as exc:
        raise ValueError(f"valuation_measures[{index}].method_kind is invalid") from exc

    return ValuationMeasureResultV2(
        measure_name=measure_name,
        value=value_decimal,
        method_kind=method_kind,
        measure_policy_id=measure_policy_id,
        bump_policy_id=bump_policy_id,
        tolerance_policy_id=tolerance_policy_id,
    )


def import_option_pricing_artifact_v2_from_canonical_payload(
    *,
    canonical_payload: str,
) -> OptionPricingArtifactV2:
    """Rehydrate governed OptionPricingArtifactV2 from canonical serialized valuation payload."""

    if not isinstance(canonical_payload, str):
        raise ValueError("canonical_payload must be a string")

    try:
        parsed = json.loads(canonical_payload)
    except json.JSONDecodeError as exc:
        raise ValueError("canonical_payload must be valid JSON") from exc

    if not isinstance(parsed, dict):
        raise ValueError("canonical_payload top-level JSON must be an object")

    keys = set(parsed.keys())
    missing = _REQUIRED_TOP_LEVEL_KEYS_V2 - keys
    extra = keys - _REQUIRED_TOP_LEVEL_KEYS_V2
    if missing:
        raise ValueError(f"canonical payload missing keys: {sorted(missing)}")
    if extra:
        raise ValueError(f"canonical payload has unexpected keys: {sorted(extra)}")

    valuation_measures_payload = parsed["valuation_measures"]
    if not isinstance(valuation_measures_payload, list):
        raise ValueError("valuation_measures must be a list")

    valuation_measures = tuple(
        _parse_measure_v2(item, index)
        for index, item in enumerate(valuation_measures_payload)
    )

    theta_contract_name = parsed["theta_roll_boundary_contract_name"]
    if theta_contract_name is not None and not isinstance(theta_contract_name, str):
        raise ValueError("theta_roll_boundary_contract_name must be string or None")

    theta_contract_version = parsed["theta_roll_boundary_contract_version"]
    if theta_contract_version is not None and not isinstance(theta_contract_version, str):
        raise ValueError("theta_roll_boundary_contract_version must be string or None")

    theta_reference = parsed["theta_roll_boundary_reference"]
    if theta_reference is not None and not isinstance(theta_reference, str):
        raise ValueError("theta_roll_boundary_reference must be string or None")

    valuation_result = OptionValuationResultV2(
        engine_name=_require_string(parsed["engine_name"], "engine_name"),
        engine_version=_require_string(parsed["engine_version"], "engine_version"),
        model_name=_require_string(parsed["model_name"], "model_name"),
        model_version=_require_string(parsed["model_version"], "model_version"),
        resolved_input_contract_name=_require_string(parsed["resolved_input_contract_name"], "resolved_input_contract_name"),
        resolved_input_contract_version=_require_string(parsed["resolved_input_contract_version"], "resolved_input_contract_version"),
        resolved_input_reference=_require_string(parsed["resolved_input_reference"], "resolved_input_reference"),
        resolved_lattice_policy_contract_name=_require_string(
            parsed["resolved_lattice_policy_contract_name"],
            "resolved_lattice_policy_contract_name",
        ),
        resolved_lattice_policy_contract_version=_require_string(
            parsed["resolved_lattice_policy_contract_version"],
            "resolved_lattice_policy_contract_version",
        ),
        resolved_lattice_policy_reference=_require_string(
            parsed["resolved_lattice_policy_reference"],
            "resolved_lattice_policy_reference",
        ),
        theta_roll_boundary_contract_name=theta_contract_name,
        theta_roll_boundary_contract_version=theta_contract_version,
        theta_roll_boundary_reference=theta_reference,
        valuation_measures=valuation_measures,
    )

    canonical_payload_hash = canonical_option_pricing_artifact_payload_hash_v2(
        valuation_result=valuation_result,
    )

    return OptionPricingArtifactV2(
        artifact_contract_name=ARTIFACT_CONTRACT_NAME_V2,
        artifact_contract_version=ARTIFACT_CONTRACT_VERSION_V2,
        valuation_result=valuation_result,
        canonical_payload_hash=canonical_payload_hash,
    )


__all__ = ["import_option_pricing_artifact_v2_from_canonical_payload"]
