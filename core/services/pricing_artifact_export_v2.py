from __future__ import annotations

from core.contracts.canonical_artifact_payload_hash_v2 import canonical_option_pricing_artifact_payload_hash_v2
from core.contracts.canonical_artifact_payload_hash_v2 import canonical_option_pricing_artifact_payload_v2
from core.contracts.canonical_artifact_payload_hash_v2 import canonical_serialize_option_pricing_artifact_payload_v2
from core.contracts.option_pricing_artifact_v2 import OptionPricingArtifactV2


def canonical_option_pricing_artifact_payload_from_artifact_v2(
    *,
    artifact: OptionPricingArtifactV2,
) -> dict[str, object]:
    """Derive canonical payload for an existing governed V2 artifact."""

    if not isinstance(artifact, OptionPricingArtifactV2):
        raise ValueError("artifact must be OptionPricingArtifactV2")

    return canonical_option_pricing_artifact_payload_v2(
        valuation_result=artifact.valuation_result,
    )


def canonical_serialize_option_pricing_artifact_from_artifact_v2(
    *,
    artifact: OptionPricingArtifactV2,
) -> str:
    """Serialize canonical payload for an existing governed V2 artifact."""

    if not isinstance(artifact, OptionPricingArtifactV2):
        raise ValueError("artifact must be OptionPricingArtifactV2")

    return canonical_serialize_option_pricing_artifact_payload_v2(
        valuation_result=artifact.valuation_result,
    )


def validate_option_pricing_artifact_payload_hash_v2(
    *,
    artifact: OptionPricingArtifactV2,
) -> str:
    """Recompute and validate canonical payload hash for an existing governed V2 artifact."""

    if not isinstance(artifact, OptionPricingArtifactV2):
        raise ValueError("artifact must be OptionPricingArtifactV2")

    computed_hash = canonical_option_pricing_artifact_payload_hash_v2(
        valuation_result=artifact.valuation_result,
    )
    if computed_hash != artifact.canonical_payload_hash:
        raise ValueError("canonical_payload_hash must match recomputed canonical V2 payload hash")
    return computed_hash


def export_option_pricing_artifact_payload_v2(
    *,
    artifact: OptionPricingArtifactV2,
) -> str:
    """Export canonical serialized payload for an existing governed V2 artifact."""

    validate_option_pricing_artifact_payload_hash_v2(
        artifact=artifact,
    )

    return canonical_serialize_option_pricing_artifact_from_artifact_v2(
        artifact=artifact,
    )


__all__ = [
    "canonical_option_pricing_artifact_payload_from_artifact_v2",
    "canonical_serialize_option_pricing_artifact_from_artifact_v2",
    "validate_option_pricing_artifact_payload_hash_v2",
    "export_option_pricing_artifact_payload_v2",
]
