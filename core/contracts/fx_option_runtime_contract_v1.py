from __future__ import annotations

from dataclasses import dataclass
import datetime
from decimal import Decimal
from decimal import InvalidOperation

from core.contracts.option_runtime_contract_v1 import SUPPORTED_EXERCISE_STYLES
from core.contracts.option_runtime_contract_v1 import SUPPORTED_OPTION_TYPES


SUPPORTED_SETTLEMENT_STYLES = {"deliverable", "non_deliverable"}


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


def _require_date(value: datetime.date, field_name: str) -> datetime.date:
    if not isinstance(value, datetime.date):
        raise ValueError(f"{field_name} must be a date")
    return value


def _require_time(value: datetime.time, field_name: str) -> datetime.time:
    if not isinstance(value, datetime.time):
        raise ValueError(f"{field_name} must be a time")
    return value


def _normalize_string_tuple(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if not isinstance(values, tuple) or len(values) == 0:
        raise ValueError(f"{field_name} must be a non-empty tuple")

    normalized: list[str] = []
    for value in values:
        normalized.append(_require_non_empty_string(value, f"{field_name} entry"))

    return tuple(normalized)


@dataclass(frozen=True)
class FxOptionRuntimeContractV1:
    """Canonical immutable FX option runtime contract with explicit economic terms."""

    contract_id: str
    currency_pair_orientation: str
    base_currency: str
    quote_currency: str
    option_type: str
    exercise_style: str
    strike: Decimal
    expiry_date: datetime.date
    expiry_cutoff_time: datetime.time
    expiry_cutoff_timezone: str
    notional: Decimal
    notional_currency_semantics: str
    premium_currency: str
    premium_payment_date: datetime.date
    settlement_style: str
    settlement_date: datetime.date
    settlement_calendar_refs: tuple[str, ...]
    fixing_source: str
    fixing_date: datetime.date
    domestic_curve_id: str
    foreign_curve_id: str
    volatility_surface_quote_convention: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "contract_id", _require_non_empty_string(self.contract_id, "contract_id"))
        object.__setattr__(
            self,
            "currency_pair_orientation",
            _require_non_empty_string(self.currency_pair_orientation, "currency_pair_orientation").lower(),
        )

        object.__setattr__(self, "base_currency", _require_currency_code(self.base_currency, "base_currency"))
        object.__setattr__(self, "quote_currency", _require_currency_code(self.quote_currency, "quote_currency"))

        option_type = _require_non_empty_string(self.option_type, "option_type").lower()
        if option_type not in SUPPORTED_OPTION_TYPES:
            raise ValueError(f"option_type must be one of {sorted(SUPPORTED_OPTION_TYPES)}")
        object.__setattr__(self, "option_type", option_type)

        exercise_style = _require_non_empty_string(self.exercise_style, "exercise_style").lower()
        if exercise_style not in SUPPORTED_EXERCISE_STYLES:
            raise ValueError(f"exercise_style must be one of {sorted(SUPPORTED_EXERCISE_STYLES)}")
        object.__setattr__(self, "exercise_style", exercise_style)

        object.__setattr__(self, "strike", _require_positive_decimal(self.strike, "strike"))
        object.__setattr__(self, "expiry_date", _require_date(self.expiry_date, "expiry_date"))
        object.__setattr__(self, "expiry_cutoff_time", _require_time(self.expiry_cutoff_time, "expiry_cutoff_time"))
        object.__setattr__(
            self,
            "expiry_cutoff_timezone",
            _require_non_empty_string(self.expiry_cutoff_timezone, "expiry_cutoff_timezone"),
        )

        object.__setattr__(self, "notional", _require_positive_decimal(self.notional, "notional"))
        object.__setattr__(
            self,
            "notional_currency_semantics",
            _require_non_empty_string(self.notional_currency_semantics, "notional_currency_semantics").lower(),
        )

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

        settlement_style = _require_non_empty_string(self.settlement_style, "settlement_style").lower()
        if settlement_style not in SUPPORTED_SETTLEMENT_STYLES:
            raise ValueError(f"settlement_style must be one of {sorted(SUPPORTED_SETTLEMENT_STYLES)}")
        object.__setattr__(self, "settlement_style", settlement_style)

        object.__setattr__(self, "settlement_date", _require_date(self.settlement_date, "settlement_date"))
        object.__setattr__(
            self,
            "settlement_calendar_refs",
            _normalize_string_tuple(self.settlement_calendar_refs, "settlement_calendar_refs"),
        )

        object.__setattr__(self, "fixing_source", _require_non_empty_string(self.fixing_source, "fixing_source"))
        object.__setattr__(self, "fixing_date", _require_date(self.fixing_date, "fixing_date"))
        object.__setattr__(self, "domestic_curve_id", _require_non_empty_string(self.domestic_curve_id, "domestic_curve_id"))
        object.__setattr__(self, "foreign_curve_id", _require_non_empty_string(self.foreign_curve_id, "foreign_curve_id"))
        object.__setattr__(
            self,
            "volatility_surface_quote_convention",
            _require_non_empty_string(
                self.volatility_surface_quote_convention,
                "volatility_surface_quote_convention",
            ),
        )


__all__ = [
    "FxOptionRuntimeContractV1",
    "SUPPORTED_SETTLEMENT_STYLES",
]
