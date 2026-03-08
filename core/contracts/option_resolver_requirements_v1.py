from __future__ import annotations

from dataclasses import dataclass

from core.contracts.fx_option_runtime_contract_v1 import SUPPORTED_SETTLEMENT_STYLES
from core.contracts.model_registry import ModelCapability
from core.contracts.option_runtime_contract_v1 import SUPPORTED_EXERCISE_STYLES
from core.contracts.option_runtime_contract_v1 import SUPPORTED_OPTION_TYPES


SUPPORTED_PAYOFF_FAMILIES = {"vanilla"}


def _require_non_empty_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    return value


def _normalize_token_tuple(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if not isinstance(values, tuple) or len(values) == 0:
        raise ValueError(f"{field_name} must be a non-empty tuple")

    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        token = _require_non_empty_string(value, f"{field_name} entry").lower()
        if token in seen:
            raise ValueError(f"{field_name} entries must be unique")
        seen.add(token)
        normalized.append(token)
    return tuple(normalized)


@dataclass(frozen=True)
class OptionValuationRequirementsV1:
    """Resolver-input contract for capability-based option valuation requests."""

    instrument_family: str
    payoff_family: str
    option_type: str
    exercise_style: str
    requested_measures: tuple[str, ...]
    required_market_inputs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "instrument_family",
            _require_non_empty_string(self.instrument_family, "instrument_family").lower(),
        )

        payoff_family = _require_non_empty_string(self.payoff_family, "payoff_family").lower()
        if payoff_family not in SUPPORTED_PAYOFF_FAMILIES:
            raise ValueError(f"payoff_family must be one of {sorted(SUPPORTED_PAYOFF_FAMILIES)}")
        object.__setattr__(self, "payoff_family", payoff_family)

        option_type = _require_non_empty_string(self.option_type, "option_type").lower()
        if option_type not in SUPPORTED_OPTION_TYPES:
            raise ValueError(f"option_type must be one of {sorted(SUPPORTED_OPTION_TYPES)}")
        object.__setattr__(self, "option_type", option_type)

        exercise_style = _require_non_empty_string(self.exercise_style, "exercise_style").lower()
        if exercise_style not in SUPPORTED_EXERCISE_STYLES:
            raise ValueError(f"exercise_style must be one of {sorted(SUPPORTED_EXERCISE_STYLES)}")
        object.__setattr__(self, "exercise_style", exercise_style)

        object.__setattr__(
            self,
            "requested_measures",
            _normalize_token_tuple(self.requested_measures, "requested_measures"),
        )
        object.__setattr__(
            self,
            "required_market_inputs",
            _normalize_token_tuple(self.required_market_inputs, "required_market_inputs"),
        )

    def required_capabilities(self) -> tuple[ModelCapability, ...]:
        """Map request dimensions into required ModelCapability tuples for matching."""

        return tuple(
            ModelCapability(
                instrument_family=self.instrument_family,
                exercise_style=self.exercise_style,
                measure=measure,
            )
            for measure in self.requested_measures
        )


@dataclass(frozen=True)
class FxOptionValuationRequirementsV1:
    """FX-specific resolver-input contract with explicit settlement dimension."""

    instrument_family: str
    payoff_family: str
    option_type: str
    exercise_style: str
    settlement_style: str
    requested_measures: tuple[str, ...]
    required_market_inputs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "instrument_family",
            _require_non_empty_string(self.instrument_family, "instrument_family").lower(),
        )

        payoff_family = _require_non_empty_string(self.payoff_family, "payoff_family").lower()
        if payoff_family not in SUPPORTED_PAYOFF_FAMILIES:
            raise ValueError(f"payoff_family must be one of {sorted(SUPPORTED_PAYOFF_FAMILIES)}")
        object.__setattr__(self, "payoff_family", payoff_family)

        option_type = _require_non_empty_string(self.option_type, "option_type").lower()
        if option_type not in SUPPORTED_OPTION_TYPES:
            raise ValueError(f"option_type must be one of {sorted(SUPPORTED_OPTION_TYPES)}")
        object.__setattr__(self, "option_type", option_type)

        exercise_style = _require_non_empty_string(self.exercise_style, "exercise_style").lower()
        if exercise_style not in SUPPORTED_EXERCISE_STYLES:
            raise ValueError(f"exercise_style must be one of {sorted(SUPPORTED_EXERCISE_STYLES)}")
        object.__setattr__(self, "exercise_style", exercise_style)

        settlement_style = _require_non_empty_string(self.settlement_style, "settlement_style").lower()
        if settlement_style not in SUPPORTED_SETTLEMENT_STYLES:
            raise ValueError(f"settlement_style must be one of {sorted(SUPPORTED_SETTLEMENT_STYLES)}")
        object.__setattr__(self, "settlement_style", settlement_style)

        object.__setattr__(
            self,
            "requested_measures",
            _normalize_token_tuple(self.requested_measures, "requested_measures"),
        )
        object.__setattr__(
            self,
            "required_market_inputs",
            _normalize_token_tuple(self.required_market_inputs, "required_market_inputs"),
        )

    def required_capabilities(self) -> tuple[ModelCapability, ...]:
        """Map FX request dimensions into required ModelCapability tuples for matching."""

        return tuple(
            ModelCapability(
                instrument_family=self.instrument_family,
                exercise_style=self.exercise_style,
                measure=measure,
            )
            for measure in self.requested_measures
        )


__all__ = [
    "FxOptionValuationRequirementsV1",
    "OptionValuationRequirementsV1",
    "SUPPORTED_PAYOFF_FAMILIES",
]
