"""FX swap boundary types for Gate F8.S1 (no pricing logic).

Defines immutable boundary contracts for FX swap near/far legs with
ILS presentation lock and deterministic validation.
"""

from __future__ import annotations

from dataclasses import dataclass
import datetime
import math


_ALLOWED_DIRECTIONS = (
    "receive_foreign_pay_domestic",
    "pay_foreign_receive_domestic",
)


def _ensure_finite(value: float, name: str) -> None:
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")


def _ensure_positive(value: float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive")


def _ensure_currency_code(value: str, name: str) -> None:
    if not isinstance(value, str) or len(value) != 3 or not value.isalpha() or not value.isupper():
        raise ValueError(f"{name} must be a 3-letter uppercase currency code")


def _opposite_direction(direction: str) -> str:
    if direction == "receive_foreign_pay_domestic":
        return "pay_foreign_receive_domestic"
    return "receive_foreign_pay_domestic"


@dataclass(frozen=True)
class FxSwapLeg:
    value_date: datetime.date
    notional_foreign: float
    forward_rate: float
    direction: str
    foreign_ccy: str
    domestic_ccy: str

    def __post_init__(self):
        _ensure_finite(self.notional_foreign, "notional_foreign")
        _ensure_positive(self.notional_foreign, "notional_foreign")

        _ensure_finite(self.forward_rate, "forward_rate")
        _ensure_positive(self.forward_rate, "forward_rate")

        if self.direction not in _ALLOWED_DIRECTIONS:
            raise ValueError("direction must be one of: receive_foreign_pay_domestic, pay_foreign_receive_domestic")

        _ensure_currency_code(self.foreign_ccy, "foreign_ccy")
        _ensure_currency_code(self.domestic_ccy, "domestic_ccy")

        if self.foreign_ccy == self.domestic_ccy:
            raise ValueError("foreign_ccy must differ from domestic_ccy")


@dataclass(frozen=True)
class FxSwapContract:
    near_leg: FxSwapLeg
    far_leg: FxSwapLeg
    reporting_ccy: str = "ILS"

    def __post_init__(self):
        if self.near_leg.value_date >= self.far_leg.value_date:
            raise ValueError("near_leg.value_date must be earlier than far_leg.value_date")

        if self.near_leg.foreign_ccy != self.far_leg.foreign_ccy:
            raise ValueError("foreign_ccy must match across near_leg and far_leg")

        if self.near_leg.domestic_ccy != self.far_leg.domestic_ccy:
            raise ValueError("domestic_ccy must match across near_leg and far_leg")

        if self.far_leg.direction != _opposite_direction(self.near_leg.direction):
            raise ValueError("far_leg.direction must be opposite of near_leg.direction")

        if self.reporting_ccy != "ILS":
            raise ValueError("reporting_ccy must be ILS")

        if self.near_leg.domestic_ccy != "ILS":
            raise ValueError("domestic_ccy must be ILS")

        if self.reporting_ccy != self.near_leg.domestic_ccy:
            raise ValueError("reporting_ccy must equal domestic_ccy")


__all__ = [
    "FxSwapLeg",
    "FxSwapContract",
]
