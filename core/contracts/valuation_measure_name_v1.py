from __future__ import annotations

from enum import Enum


class ValuationMeasureNameV1(str, Enum):
    """Closed canonical Phase C valuation measure names for single-trade FX options."""

    PRESENT_VALUE = "present_value"
    INTRINSIC_VALUE = "intrinsic_value"
    TIME_VALUE = "time_value"
    DELTA_SPOT_NON_PREMIUM_ADJUSTED = "delta_spot_non_premium_adjusted"
    GAMMA_SPOT = "gamma_spot"
    VEGA_1VOL_ABS = "vega_1vol_abs"
    THETA_1D_CALENDAR = "theta_1d_calendar"
    RHO_DOMESTIC_1PCT = "rho_domestic_1pct"
    RHO_FOREIGN_1PCT = "rho_foreign_1pct"


__all__ = ["ValuationMeasureNameV1"]
