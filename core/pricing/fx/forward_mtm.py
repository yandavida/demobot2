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
    # Validate as_of_ts consistency
    if as_of_ts != market_snapshot.as_of_ts:
        raise ValueError(
            f"as_of_ts mismatch: valuation={as_of_ts}, snapshot={market_snapshot.as_of_ts}"
        )
    
    # Extract and validate required contract parameters
    if contract.forward_rate is None:
        raise ValueError("forward_rate is required for FX forward pricing")
    K = contract.forward_rate
    
    if contract.direction is None:
        raise ValueError("direction is required for FX forward pricing")
    direction = contract.direction
    
    Nf = contract.notional
    
    # Extract and validate required market inputs
    S = market_snapshot.spot_rate
    
    if market_snapshot.df_domestic is None:
        raise ValueError("df_domestic is required for FX forward pricing")
    DFd = market_snapshot.df_domestic
    
    if market_snapshot.df_foreign is None:
        raise ValueError("df_foreign is required for FX forward pricing")
    DFf = market_snapshot.df_foreign
    
    # Compute market forward rate
    F_mkt = S * DFf / DFd
    
    # Compute close-out PV using formula (B): PV = Nf * DFd * (F_mkt - K)
    # This is algebraically equivalent to (A): PV = Nf * (S * DFf - K * DFd)
    pv_unsigned = Nf * DFd * (F_mkt - K)
    
    # Apply sign based on direction
    if direction == "receive_foreign_pay_domestic":
        # Positive when F_mkt > K (we receive foreign at market forward, pay at K)
        pv = pv_unsigned
    elif direction == "pay_foreign_receive_domestic":
        # Negative when F_mkt > K (we pay foreign at market forward, receive at K)
        pv = -pv_unsigned
    else:
        raise ValueError(f"Invalid contract direction: {direction}")
    
    # Build result with details
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


__all__ = ["price_fx_forward"]
