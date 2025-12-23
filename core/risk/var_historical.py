from __future__ import annotations
import math
from typing import Sequence, Optional
from core.risk.var_types import VarResult
from core.portfolio.models import Currency

def calc_historical_var(*, pnl_series: Sequence[float], confidence: float) -> float:
    """
    Computes Historical VaR using the nearest-rank quantile method.
    pnl_series: sequence of P&L (ΔPV) observations in base currency.
    Negative values are losses, positive are gains.
    Returns: VaR as a positive loss number (>=0).
    Quantile method: nearest-rank (sorted, index = ceil(alpha * n) - 1, clamp to [0, n-1])
    """
    n = len(pnl_series)
    if n < 20:
        raise ValueError(f"pnl_series must have at least 20 observations, got {n}")
    if not (0.5 < confidence < 1.0):
        raise ValueError(f"confidence must be in (0.5, 1.0), got {confidence}")
    alpha = 1.0 - confidence
    sorted_pnl = sorted(pnl_series)
    idx = max(0, min(n - 1, math.ceil(alpha * n) - 1))
    q = sorted_pnl[idx]
    var = max(0.0, -q)
    return float(var)

def build_historical_var_result(
    *,
    pnl_series: Sequence[float],
    confidence: float,
    horizon_days: int,
    currency: Currency,
    notes: Optional[dict[str, str]] = None,
) -> VarResult:
    """
    Helper to produce a VarResult for historical VaR (no CVaR yet).
    """
    var = calc_historical_var(pnl_series=pnl_series, confidence=confidence)
    return VarResult(
        method="historical",
        confidence=confidence,
        horizon_days=horizon_days,
        currency=currency,
        var=var,
        cvar=None,
        notes=notes or {},
    )
