from __future__ import annotations

import datetime
from typing import Optional, Protocol

from core.pricing.fx import types as fx_types


class FXForwardPricingKernel(Protocol):
    def price_forward(
        self,
        as_of_ts: datetime.datetime,
        contract: fx_types.FXForwardContract,
        market_snapshot: fx_types.FxMarketSnapshot,
        conventions: Optional[fx_types.FxConventions],
    ) -> fx_types.PricingResult:
        ...


class DefaultFXForwardKernel:
    def price_forward(
        self,
        as_of_ts: datetime.datetime,
        contract: fx_types.FXForwardContract,
        market_snapshot: fx_types.FxMarketSnapshot,
        conventions: Optional[fx_types.FxConventions],
    ) -> fx_types.PricingResult:
        # conventions is intentionally unused in F8.2/F8.M2 formula path
        _ = conventions

        if as_of_ts != market_snapshot.as_of_ts:
            raise ValueError(
                f"as_of_ts mismatch: valuation={as_of_ts}, snapshot={market_snapshot.as_of_ts}"
            )

        if contract.forward_rate is None:
            raise ValueError("forward_rate is required for FX forward pricing")
        K = contract.forward_rate

        if contract.direction is None:
            raise ValueError("direction is required for FX forward pricing")
        direction = contract.direction

        Nf = contract.notional
        S = market_snapshot.spot_rate

        if market_snapshot.df_domestic is None:
            raise ValueError("df_domestic is required for FX forward pricing")
        DFd = market_snapshot.df_domestic

        if market_snapshot.df_foreign is None:
            raise ValueError("df_foreign is required for FX forward pricing")
        DFf = market_snapshot.df_foreign

        F_mkt = S * DFf / DFd
        pv_unsigned = Nf * DFd * (F_mkt - K)

        if direction == "receive_foreign_pay_domestic":
            pv = pv_unsigned
        elif direction == "pay_foreign_receive_domestic":
            pv = -pv_unsigned
        else:
            raise ValueError(f"Invalid contract direction: {direction}")

        details = {
            "forward_market": F_mkt,
            "spot": S,
            "df_domestic": DFd,
            "df_foreign": DFf,
            "forward_rate": K,
            "notional_foreign": Nf,
            "direction": direction,
        }

        return fx_types.PricingResult(
            as_of_ts=as_of_ts,
            pv=pv,
            details=details,
        )


__all__ = ["FXForwardPricingKernel", "DefaultFXForwardKernel"]
