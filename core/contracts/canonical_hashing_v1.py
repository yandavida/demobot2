from __future__ import annotations

import hashlib

from core.contracts.canonical_serialization_v1 import canonical_serialize_option_pricing_artifact_payload_v1
from core.contracts.option_valuation_result_v1 import OptionValuationResultV1


CANONICAL_HASH_ALGORITHM_V1 = "sha256"


def canonical_hash_from_serialized_payload_v1(serialized_payload: str) -> str:
    """Compute deterministic hash from canonical UTF-8 payload text."""

    if not isinstance(serialized_payload, str):
        raise ValueError("serialized_payload must be a string")

    if CANONICAL_HASH_ALGORITHM_V1 != "sha256":
        raise ValueError("unsupported canonical hash algorithm")

    payload_bytes = serialized_payload.encode("utf-8")
    return hashlib.sha256(payload_bytes).hexdigest()


def canonical_option_pricing_artifact_hash_v1(
    *,
    artifact_contract_name: str,
    artifact_contract_version: str,
    valuation_result: OptionValuationResultV1,
) -> str:
    """Compute canonical SHA-256 hash for governed option pricing artifact payload."""

    serialized_payload = canonical_serialize_option_pricing_artifact_payload_v1(
        artifact_contract_name=artifact_contract_name,
        artifact_contract_version=artifact_contract_version,
        valuation_result=valuation_result,
    )
    return canonical_hash_from_serialized_payload_v1(serialized_payload)


__all__ = [
    "CANONICAL_HASH_ALGORITHM_V1",
    "canonical_hash_from_serialized_payload_v1",
    "canonical_option_pricing_artifact_hash_v1",
]
