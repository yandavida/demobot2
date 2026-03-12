from __future__ import annotations

from core.contracts.canonical_artifact_payload_hash_v2 import canonical_option_pricing_artifact_payload_hash_v2
from core.contracts.option_pricing_artifact_v2 import ARTIFACT_CONTRACT_NAME_V2
from core.contracts.option_pricing_artifact_v2 import ARTIFACT_CONTRACT_VERSION_V2
from core.contracts.option_pricing_artifact_v2 import OptionPricingArtifactV2
from core.contracts.option_valuation_result_v2 import OptionValuationResultV2


def build_option_pricing_artifact_v2(
    *,
    valuation_result: OptionValuationResultV2,
) -> OptionPricingArtifactV2:
    """Build deterministic governed V2 artifact from explicit valuation result input only."""

    if not isinstance(valuation_result, OptionValuationResultV2):
        raise ValueError("valuation_result must be OptionValuationResultV2")

    canonical_payload_hash = canonical_option_pricing_artifact_payload_hash_v2(
        valuation_result=valuation_result,
    )

    return OptionPricingArtifactV2(
        artifact_contract_name=ARTIFACT_CONTRACT_NAME_V2,
        artifact_contract_version=ARTIFACT_CONTRACT_VERSION_V2,
        valuation_result=valuation_result,
        canonical_payload_hash=canonical_payload_hash,
    )


__all__ = [
    "build_option_pricing_artifact_v2",
]
