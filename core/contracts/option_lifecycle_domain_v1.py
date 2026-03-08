from __future__ import annotations

from dataclasses import dataclass
import datetime
from decimal import Decimal
from decimal import InvalidOperation

from core.contracts.fx_option_runtime_contract_v1 import FxOptionRuntimeContractV1
from core.contracts.fx_option_runtime_contract_v1 import SUPPORTED_SETTLEMENT_STYLES
from core.contracts.option_runtime_contract_v1 import OptionRuntimeContractV1


SUPPORTED_LIFECYCLE_EVENT_TYPES = {
    "expiry",
    "exercise",
    "assignment",
    "settlement_outcome",
}
SUPPORTED_LIFECYCLE_OUTCOME_STATES = {
    "expired",
    "exercised",
    "assigned",
    "settled",
}


def _require_non_empty_string(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    return value


def _require_currency_code(value: str, field_name: str) -> str:
    normalized = _require_non_empty_string(value, field_name).upper()
    if len(normalized) != 3 or not normalized.isalpha():
        raise ValueError(f"{field_name} must be a 3-letter currency code")
    return normalized


def _require_positive_decimal(value: Decimal | str | int | float, field_name: str) -> Decimal:
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a valid decimal") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if decimal_value <= 0:
        raise ValueError(f"{field_name} must be > 0")
    return decimal_value


def _require_datetime(value: datetime.datetime, field_name: str) -> datetime.datetime:
    if not isinstance(value, datetime.datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def _require_date(value: datetime.date, field_name: str) -> datetime.date:
    if not isinstance(value, datetime.date):
        raise ValueError(f"{field_name} must be a date")
    return value


@dataclass(frozen=True)
class OptionLifecycleEventRefV1:
    """Lifecycle event reference vocabulary without processing behavior."""

    event_id: str
    contract_id: str
    event_type: str
    event_timestamp: datetime.datetime
    valuation_context_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_id", _require_non_empty_string(self.event_id, "event_id"))
        object.__setattr__(self, "contract_id", _require_non_empty_string(self.contract_id, "contract_id"))

        event_type = _require_non_empty_string(self.event_type, "event_type").lower()
        if event_type not in SUPPORTED_LIFECYCLE_EVENT_TYPES:
            raise ValueError(
                f"event_type must be one of {sorted(SUPPORTED_LIFECYCLE_EVENT_TYPES)}"
            )
        object.__setattr__(self, "event_type", event_type)

        object.__setattr__(
            self,
            "event_timestamp",
            _require_datetime(self.event_timestamp, "event_timestamp"),
        )
        object.__setattr__(
            self,
            "valuation_context_id",
            _require_non_empty_string(self.valuation_context_id, "valuation_context_id"),
        )


@dataclass(frozen=True)
class OptionPremiumCashflowRefV1:
    """Explicit premium cashflow semantics reference for lifecycle outcomes."""

    premium_cashflow_id: str
    contract_id: str
    premium_currency: str
    premium_payment_date: datetime.date
    premium_amount: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "premium_cashflow_id",
            _require_non_empty_string(self.premium_cashflow_id, "premium_cashflow_id"),
        )
        object.__setattr__(self, "contract_id", _require_non_empty_string(self.contract_id, "contract_id"))
        object.__setattr__(
            self,
            "premium_currency",
            _require_currency_code(self.premium_currency, "premium_currency"),
        )
        object.__setattr__(
            self,
            "premium_payment_date",
            _require_date(self.premium_payment_date, "premium_payment_date"),
        )
        object.__setattr__(
            self,
            "premium_amount",
            _require_positive_decimal(self.premium_amount, "premium_amount"),
        )


@dataclass(frozen=True)
class OptionSettlementOutcomeV1:
    """Explicit settlement outcome reference semantics for lifecycle boundaries."""

    settlement_outcome_id: str
    contract_id: str
    settlement_style: str
    settlement_date: datetime.date
    settlement_currency: str
    settlement_amount: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "settlement_outcome_id",
            _require_non_empty_string(self.settlement_outcome_id, "settlement_outcome_id"),
        )
        object.__setattr__(self, "contract_id", _require_non_empty_string(self.contract_id, "contract_id"))

        settlement_style = _require_non_empty_string(self.settlement_style, "settlement_style").lower()
        if settlement_style not in SUPPORTED_SETTLEMENT_STYLES:
            raise ValueError(
                f"settlement_style must be one of {sorted(SUPPORTED_SETTLEMENT_STYLES)}"
            )
        object.__setattr__(self, "settlement_style", settlement_style)

        object.__setattr__(self, "settlement_date", _require_date(self.settlement_date, "settlement_date"))
        object.__setattr__(
            self,
            "settlement_currency",
            _require_currency_code(self.settlement_currency, "settlement_currency"),
        )
        object.__setattr__(
            self,
            "settlement_amount",
            _require_positive_decimal(self.settlement_amount, "settlement_amount"),
        )


@dataclass(frozen=True)
class OptionPostEventRecomputeRefV1:
    """Post-event recomputation reference semantics without recomputation logic."""

    recompute_ref_id: str
    source_event_id: str
    valuation_context_id: str
    valuation_dependency_bundle_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "recompute_ref_id",
            _require_non_empty_string(self.recompute_ref_id, "recompute_ref_id"),
        )
        object.__setattr__(
            self,
            "source_event_id",
            _require_non_empty_string(self.source_event_id, "source_event_id"),
        )
        object.__setattr__(
            self,
            "valuation_context_id",
            _require_non_empty_string(self.valuation_context_id, "valuation_context_id"),
        )
        object.__setattr__(
            self,
            "valuation_dependency_bundle_id",
            _require_non_empty_string(
                self.valuation_dependency_bundle_id,
                "valuation_dependency_bundle_id",
            ),
        )


@dataclass(frozen=True)
class OptionLifecycleOutcomeV1:
    """Lifecycle outcome boundary contract composed of explicit lifecycle refs."""

    option_contract: OptionRuntimeContractV1 | FxOptionRuntimeContractV1
    lifecycle_event: OptionLifecycleEventRefV1
    outcome_state: str
    premium_cashflow_ref: OptionPremiumCashflowRefV1
    settlement_outcome: OptionSettlementOutcomeV1
    post_event_recompute_ref: OptionPostEventRecomputeRefV1

    def __post_init__(self) -> None:
        if not isinstance(self.option_contract, (OptionRuntimeContractV1, FxOptionRuntimeContractV1)):
            raise ValueError(
                "option_contract must be OptionRuntimeContractV1 or FxOptionRuntimeContractV1"
            )

        outcome_state = _require_non_empty_string(self.outcome_state, "outcome_state").lower()
        if outcome_state not in SUPPORTED_LIFECYCLE_OUTCOME_STATES:
            raise ValueError(
                f"outcome_state must be one of {sorted(SUPPORTED_LIFECYCLE_OUTCOME_STATES)}"
            )
        object.__setattr__(self, "outcome_state", outcome_state)


__all__ = [
    "OptionLifecycleEventRefV1",
    "OptionLifecycleOutcomeV1",
    "OptionPostEventRecomputeRefV1",
    "OptionPremiumCashflowRefV1",
    "OptionSettlementOutcomeV1",
    "SUPPORTED_LIFECYCLE_EVENT_TYPES",
    "SUPPORTED_LIFECYCLE_OUTCOME_STATES",
]
