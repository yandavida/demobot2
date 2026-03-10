from __future__ import annotations

from core.contracts.canonical_hashing_v1 import canonical_option_pricing_artifact_hash_v1
from core.contracts.option_pricing_artifact_v1 import OptionPricingArtifactV1
from core.contracts.option_valuation_result_v1 import OptionValuationResultV1


ARTIFACT_CONTRACT_NAME_V1 = "OptionPricingArtifactV1"
ARTIFACT_CONTRACT_VERSION_V1 = "1.0.0"


def build_option_pricing_artifact_v1(
    *,
    valuation_result: OptionValuationResultV1,
) -> OptionPricingArtifactV1:
    """Build deterministic governed artifact from explicit valuation result input only."""

    if not isinstance(valuation_result, OptionValuationResultV1):
        raise ValueError("valuation_result must be OptionValuationResultV1")

    canonical_payload_hash = canonical_option_pricing_artifact_hash_v1(
        artifact_contract_name=ARTIFACT_CONTRACT_NAME_V1,
        artifact_contract_version=ARTIFACT_CONTRACT_VERSION_V1,
        valuation_result=valuation_result,
    )

    return OptionPricingArtifactV1(
        artifact_contract_name=ARTIFACT_CONTRACT_NAME_V1,
        artifact_contract_version=ARTIFACT_CONTRACT_VERSION_V1,
        valuation_result=valuation_result,
        canonical_payload_hash=canonical_payload_hash,
    )


__all__ = [
    "ARTIFACT_CONTRACT_NAME_V1",
    "ARTIFACT_CONTRACT_VERSION_V1",
    "build_option_pricing_artifact_v1",
]
