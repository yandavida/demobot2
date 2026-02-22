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
        from core.pricing.fx import forward_mtm

        return forward_mtm.price_fx_forward(
            as_of_ts=as_of_ts,
            contract=contract,
            market_snapshot=market_snapshot,
            conventions=conventions,
        )


__all__ = ["FXForwardPricingKernel", "DefaultFXForwardKernel"]
