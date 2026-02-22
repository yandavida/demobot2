from __future__ import annotations

import datetime
from dataclasses import dataclass
import math

from core.pricing.fx.forward_mtm import price_fx_forward
from core.pricing.fx.types import FXForwardContract, FxMarketSnapshot, PricingResult
from core.pricing.fx.valuation_context import ValuationContext


_ALLOWED_DIRECTIONS = (
    "receive_foreign_pay_domestic",
    "pay_foreign_receive_domestic",
)


def _ensure_finite(value: float, field_name: str) -> None:
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{field_name} must be finite")


@dataclass(frozen=True, slots=True)
class FxSwapLeg:
    forward_rate: float
    direction: str
    settlement_date: datetime.date

    def __post_init__(self):
        _ensure_finite(self.forward_rate, "forward_rate")

        if self.direction not in _ALLOWED_DIRECTIONS:
            raise ValueError("direction must be one of: receive_foreign_pay_domestic, pay_foreign_receive_domestic")


@dataclass(frozen=True, slots=True)
class FxSwapContract:
    base_ccy: str
    quote_ccy: str
    notional_foreign: float
    near: FxSwapLeg
    far: FxSwapLeg

    def __post_init__(self):
        _ensure_finite(self.notional_foreign, "notional_foreign")

        if self.base_ccy == self.quote_ccy:
            raise ValueError("base_ccy and quote_ccy must differ")

        if self.near.settlement_date >= self.far.settlement_date:
            raise ValueError("near.settlement_date must be earlier than far.settlement_date")


def price_fx_swap(
    as_of_ts: datetime.datetime,
    contract: FxSwapContract,
    market_near: FxMarketSnapshot,
    market_far: FxMarketSnapshot,
) -> PricingResult:
    near_contract = FXForwardContract(
        base_currency=contract.base_ccy,
        quote_currency=contract.quote_ccy,
        notional=contract.notional_foreign,
        forward_date=contract.near.settlement_date,
        forward_rate=contract.near.forward_rate,
        direction=contract.near.direction,
    )
    far_contract = FXForwardContract(
        base_currency=contract.base_ccy,
        quote_currency=contract.quote_ccy,
        notional=contract.notional_foreign,
        forward_date=contract.far.settlement_date,
        forward_rate=contract.far.forward_rate,
        direction=contract.far.direction,
    )

    near_result = price_fx_forward(as_of_ts, near_contract, market_near, market_near.conventions)
    far_result = price_fx_forward(as_of_ts, far_contract, market_far, market_far.conventions)

    pv_total = near_result.pv + far_result.pv

    details = {
        "pv_near": near_result.pv,
        "pv_far": far_result.pv,
        "forward_market_near": near_result.details["forward_market"],
        "forward_market_far": far_result.details["forward_market"],
    }

    return PricingResult(
        as_of_ts=as_of_ts,
        pv=pv_total,
        details=details,
    )


def price_fx_swap_ctx(
    context: ValuationContext,
    swap_contract: FxSwapContract,
    near_snapshot: FxMarketSnapshot,
    far_snapshot: FxMarketSnapshot,
    conventions=None,
    *,
    kernel=None,
) -> PricingResult:
    if context.strict_mode:
        if (
            near_snapshot.as_of_ts != context.as_of_ts
            or far_snapshot.as_of_ts != context.as_of_ts
        ):
            raise ValueError("swap snapshots as_of_ts must equal context.as_of_ts")

    _ = conventions
    _ = kernel

    return price_fx_swap(
        as_of_ts=context.as_of_ts,
        contract=swap_contract,
        market_near=near_snapshot,
        market_far=far_snapshot,
    )


__all__ = ["FxSwapLeg", "FxSwapContract", "price_fx_swap", "price_fx_swap_ctx"]
