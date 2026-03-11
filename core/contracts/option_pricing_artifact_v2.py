from __future__ import annotations

from dataclasses import dataclass

from core.contracts.option_valuation_result_v2 import OptionValuationResultV2


ARTIFACT_CONTRACT_NAME_V2 = "OptionPricingArtifactV2"
ARTIFACT_CONTRACT_VERSION_V2 = "2.0.0"


def _require_non_empty_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    return value


def _require_exact_identity(value: str, field_name: str, expected: str) -> str:
    normalized = _require_non_empty_string(value, field_name)
    if normalized != expected:
        raise ValueError(f"{field_name} must equal {expected}")
    return normalized


def _require_sha256_hex(value: str, field_name: str) -> str:
    normalized = _require_non_empty_string(value, field_name)
    if len(normalized) != 64:
        raise ValueError(f"{field_name} must be a 64-char lowercase sha256 hex digest")
    for char in normalized:
        if char not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a 64-char lowercase sha256 hex digest")
    return normalized


@dataclass(frozen=True)
class OptionPricingArtifactV2:
    """Immutable governed artifact contract for single-trade Phase D option pricing outputs."""

    artifact_contract_name: str
    artifact_contract_version: str
    valuation_result: OptionValuationResultV2
    canonical_payload_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "artifact_contract_name",
            _require_exact_identity(
                self.artifact_contract_name,
                "artifact_contract_name",
                ARTIFACT_CONTRACT_NAME_V2,
            ),
        )
        object.__setattr__(
            self,
            "artifact_contract_version",
            _require_exact_identity(
                self.artifact_contract_version,
                "artifact_contract_version",
                ARTIFACT_CONTRACT_VERSION_V2,
            ),
        )
        if not isinstance(self.valuation_result, OptionValuationResultV2):
            raise ValueError("valuation_result must be OptionValuationResultV2")
        object.__setattr__(
            self,
            "canonical_payload_hash",
            _require_sha256_hex(self.canonical_payload_hash, "canonical_payload_hash"),
        )


__all__ = [
    "ARTIFACT_CONTRACT_NAME_V2",
    "ARTIFACT_CONTRACT_VERSION_V2",
    "OptionPricingArtifactV2",
]