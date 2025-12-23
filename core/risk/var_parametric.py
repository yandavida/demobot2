from __future__ import annotations
import math
from statistics import NormalDist

def calc_parametric_var(*, sigma_pv_1d: float, confidence: float, horizon_days: int) -> float:
    """
    Parametric VaR (mean=0): VaR = z(confidence) * sigma_pv_1d * sqrt(horizon_days)
    Returns positive float (VaR >= 0)
    Raises ValueError for invalid sigma or horizon.
    """
    if sigma_pv_1d < 0:
        raise ValueError(f"sigma_pv_1d must be >= 0, got {sigma_pv_1d}")
    if horizon_days <= 0:
        raise ValueError(f"horizon_days must be > 0, got {horizon_days}")
    if not (0 < confidence < 1):
        raise ValueError(f"confidence must be in (0, 1), got {confidence}")
    z = NormalDist().inv_cdf(confidence)
    var = abs(z) * sigma_pv_1d * math.sqrt(horizon_days)
    return float(abs(var))
