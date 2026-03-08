from __future__ import annotations

from dataclasses import dataclass
import datetime
from decimal import Decimal
from decimal import InvalidOperation


SUPPORTED_OPTION_TYPES = {"call", "put"}
SUPPORTED_EXERCISE_STYLES = {"european", "american"}


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


@dataclass(frozen=True)
class OptionRuntimeContractV1:
    """Canonical immutable runtime contract for a generic option instrument."""

    contract_id: str
    underlying_instrument_ref: str
    option_type: str
    exercise_style: str
    strike: Decimal
    expiry_date: datetime.date
    notional: Decimal
    notional_currency: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "contract_id", _require_non_empty_string(self.contract_id, "contract_id"))
        object.__setattr__(
            self,
            "underlying_instrument_ref",
            _require_non_empty_string(self.underlying_instrument_ref, "underlying_instrument_ref"),
        )

        option_type = _require_non_empty_string(self.option_type, "option_type").lower()
        if option_type not in SUPPORTED_OPTION_TYPES:
            raise ValueError(f"option_type must be one of {sorted(SUPPORTED_OPTION_TYPES)}")
        object.__setattr__(self, "option_type", option_type)

        exercise_style = _require_non_empty_string(self.exercise_style, "exercise_style").lower()
        if exercise_style not in SUPPORTED_EXERCISE_STYLES:
            raise ValueError(f"exercise_style must be one of {sorted(SUPPORTED_EXERCISE_STYLES)}")
        object.__setattr__(self, "exercise_style", exercise_style)

        object.__setattr__(self, "strike", _require_positive_decimal(self.strike, "strike"))

        if not isinstance(self.expiry_date, datetime.date):
            raise ValueError("expiry_date must be a date")

        object.__setattr__(self, "notional", _require_positive_decimal(self.notional, "notional"))
        object.__setattr__(
            self,
            "notional_currency",
            _require_currency_code(self.notional_currency, "notional_currency"),
        )


__all__ = [
    "OptionRuntimeContractV1",
    "SUPPORTED_EXERCISE_STYLES",
    "SUPPORTED_OPTION_TYPES",
]
