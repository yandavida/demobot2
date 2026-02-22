"""Gate F8.2: FX Forward MTM close-out PV (bank-standard).

Implements ISA-compliant close-out valuation for FX forward contracts.
PV = close-out amount at as_of_ts (end-of-day valuation point).

Uses only objective market inputs from snapshot. Fails deterministically
if required inputs are missing.

Bank-standard formulas (both must be consistent):
(A) PV = Nf * (S * DFf(T) - K * DFd(T))
(B) PV = Nf * DFd(T) * (F_mkt - K), where F_mkt = S * DFf(T) / DFd(T)

Sign convention:
- receive_foreign_pay_domestic: PV increases when F_mkt > K
- pay_foreign_receive_domestic: PV decreases when F_mkt > K (opposite sign)
"""
from __future__ import annotations

import datetime
from typing import Optional

from core.pricing.fx import types as fx_types
from core.pricing.fx.kernels import DefaultFXForwardKernel


_DEFAULT_KERNEL = DefaultFXForwardKernel()


def price_fx_forward(
    as_of_ts: datetime.datetime,
    contract: fx_types.FXForwardContract,
    market_snapshot: fx_types.FxMarketSnapshot,
    conventions: Optional[fx_types.FxConventions],
) -> fx_types.PricingResult:
    """Compute close-out PV for FX forward contract (bank-standard).
    
    Args:
        as_of_ts: Valuation timestamp (must match snapshot.as_of_ts)
        contract: FX forward contract with notional, forward_rate, direction
        market_snapshot: Market data with spot_rate, df_domestic, df_foreign
        conventions: Optional conventions (unused in F8.2)
    
    Returns:
        PricingResult with pv (domestic currency), as_of_ts, and details
    
    Raises:
        ValueError: If required market inputs are missing or as_of_ts mismatch
    """
    return _DEFAULT_KERNEL.price_forward(
        as_of_ts=as_of_ts,
        contract=contract,
        market_snapshot=market_snapshot,
        conventions=conventions,
    )


__all__ = ["price_fx_forward"]
