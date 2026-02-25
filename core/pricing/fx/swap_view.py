from __future__ import annotations

from dataclasses import dataclass
import datetime
import math
from typing import Optional

from core.pricing.fx.valuation_context import ValuationContext


_ALLOWED_DIRECTIONS = (
    "receive_foreign_pay_domestic",
    "pay_foreign_receive_domestic",
)


def _ensure_finite(value: float, name: str) -> None:
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def _ensure_non_empty(value: str, name: str) -> None:
    if value.strip() == "":
        raise ValueError(f"{name} must be non-empty")


@dataclass(frozen=True, slots=True)
class FxCashflow:
    amount: float
    currency: str
    settlement_date: datetime.date

    def __post_init__(self) -> None:
        _ensure_finite(self.amount, "amount")
        _ensure_non_empty(self.currency, "currency")
        if self.settlement_date is None:
            raise ValueError("settlement_date is required")


@dataclass(frozen=True, slots=True)
class FxSwapLegCashflows:
    leg_id: str
    settlement_date: datetime.date
    foreign: FxCashflow
    domestic: FxCashflow
    forward_rate: float
    direction: str

    def __post_init__(self) -> None:
        _ensure_non_empty(self.leg_id, "leg_id")
        if self.settlement_date is None:
            raise ValueError("settlement_date is required")
        _ensure_finite(self.forward_rate, "forward_rate")
        if self.direction not in _ALLOWED_DIRECTIONS:
            raise ValueError("direction must be one of: receive_foreign_pay_domestic, pay_foreign_receive_domestic")

        if self.foreign.settlement_date != self.settlement_date:
            raise ValueError("foreign settlement_date must equal leg settlement_date")
        if self.domestic.settlement_date != self.settlement_date:
            raise ValueError("domestic settlement_date must equal leg settlement_date")


@dataclass(frozen=True, slots=True)
class FxSwapCashflowView:
    as_of_ts: datetime.datetime
    domestic_currency: str
    foreign_currency: str
    legs: tuple[FxSwapLegCashflows, FxSwapLegCashflows]

    def __post_init__(self) -> None:
        if self.as_of_ts.tzinfo is None:
            raise ValueError("as_of_ts must be timezone-aware")
        _ensure_non_empty(self.domestic_currency, "domestic_currency")
        _ensure_non_empty(self.foreign_currency, "foreign_currency")

        if len(self.legs) != 2:
            raise ValueError("legs must contain exactly 2 items")
        if self.legs[0].leg_id != "near" or self.legs[1].leg_id != "far":
            raise ValueError("legs must be ordered as near then far")


# Contractual settlement cashflow math (per leg i):
# If direction_i == receive_foreign_pay_domestic:
#   foreign_cashflow_i = +Nf_i
#   domestic_cashflow_i = -Nf_i * K_i
# If direction_i == pay_foreign_receive_domestic:
#   foreign_cashflow_i = -Nf_i
#   domestic_cashflow_i = +Nf_i * K_i
# This is settlement exchange only (not PV/discounted MTM).
def _build_leg_cashflows(
    *,
    leg_id: str,
    settlement_date: datetime.date,
    notional_foreign: float,
    forward_rate: float,
    direction: str,
    foreign_currency: str,
    domestic_currency: str,
) -> FxSwapLegCashflows:
    if settlement_date is None:
        raise ValueError("settlement_date is required")
    _ensure_finite(notional_foreign, "notional_foreign")
    _ensure_finite(forward_rate, "forward_rate")
    if direction not in _ALLOWED_DIRECTIONS:
        raise ValueError("direction must be one of: receive_foreign_pay_domestic, pay_foreign_receive_domestic")

    notional = abs(notional_foreign)

    if direction == "receive_foreign_pay_domestic":
        foreign_amount = notional
        domestic_amount = -(notional * forward_rate)
    else:
        foreign_amount = -notional
        domestic_amount = notional * forward_rate

    foreign_cf = FxCashflow(
        amount=foreign_amount,
        currency=foreign_currency,
        settlement_date=settlement_date,
    )
    domestic_cf = FxCashflow(
        amount=domestic_amount,
        currency=domestic_currency,
        settlement_date=settlement_date,
    )

    return FxSwapLegCashflows(
        leg_id=leg_id,
        settlement_date=settlement_date,
        foreign=foreign_cf,
        domestic=domestic_cf,
        forward_rate=forward_rate,
        direction=direction,
    )


def _resolve_domestic_currency(context: ValuationContext, conventions: Optional[object]) -> str:
    domestic_from_conventions = getattr(conventions, "domestic_currency", None)
    if isinstance(domestic_from_conventions, str) and domestic_from_conventions.strip() != "":
        if domestic_from_conventions != context.domestic_currency:
            raise ValueError("conventions.domestic_currency must match context.domestic_currency")
    return context.domestic_currency


def build_fx_swap_cashflow_view(
    context: ValuationContext,
    swap_contract,
    *,
    conventions=None,
) -> FxSwapCashflowView:
    domestic_currency = _resolve_domestic_currency(context, conventions)
    foreign_currency = swap_contract.base_ccy

    _ensure_non_empty(domestic_currency, "domestic_currency")
    _ensure_non_empty(foreign_currency, "foreign_currency")

    near_leg = _build_leg_cashflows(
        leg_id="near",
        settlement_date=swap_contract.near.settlement_date,
        notional_foreign=swap_contract.notional_foreign,
        forward_rate=swap_contract.near.forward_rate,
        direction=swap_contract.near.direction,
        foreign_currency=foreign_currency,
        domestic_currency=domestic_currency,
    )
    far_leg = _build_leg_cashflows(
        leg_id="far",
        settlement_date=swap_contract.far.settlement_date,
        notional_foreign=swap_contract.notional_foreign,
        forward_rate=swap_contract.far.forward_rate,
        direction=swap_contract.far.direction,
        foreign_currency=foreign_currency,
        domestic_currency=domestic_currency,
    )

    return FxSwapCashflowView(
        as_of_ts=context.as_of_ts,
        domestic_currency=domestic_currency,
        foreign_currency=foreign_currency,
        legs=(near_leg, far_leg),
    )


__all__ = [
    "FxCashflow",
    "FxSwapLegCashflows",
    "FxSwapCashflowView",
    "build_fx_swap_cashflow_view",
]
