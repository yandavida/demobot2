from __future__ import annotations

from core.contracts.canonical_hashing_v1 import canonical_option_pricing_artifact_hash_v1
from core.contracts.option_pricing_artifact_v1 import OptionPricingArtifactV1
from core.contracts.option_valuation_result_v1 import OptionValuationResultV1


def build_option_pricing_artifact_v1(
    *,
    artifact_contract_name: str,
    artifact_contract_version: str,
    valuation_result: OptionValuationResultV1,
) -> OptionPricingArtifactV1:
    """Build deterministic pricing artifact from explicit valuation result input only."""

    canonical_payload_hash = canonical_option_pricing_artifact_hash_v1(
        artifact_contract_name=artifact_contract_name,
        artifact_contract_version=artifact_contract_version,
        valuation_result=valuation_result,
    )

    return OptionPricingArtifactV1(
        artifact_contract_name=artifact_contract_name,
        artifact_contract_version=artifact_contract_version,
        valuation_result=valuation_result,
        canonical_payload_hash=canonical_payload_hash,
    )


__all__ = ["build_option_pricing_artifact_v1"]
