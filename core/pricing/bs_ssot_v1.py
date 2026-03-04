from __future__ import annotations

from dataclasses import dataclass
import math

from core.numeric_policy import DEFAULT_TOLERANCES
from core.numeric_policy import MetricClass
from core.pricing.bs import bs_price


TIME_FRACTION_POLICY_ACT_365F = "ACT_365F"


def _tol_abs(metric: MetricClass) -> float:
    return float(DEFAULT_TOLERANCES[metric].abs or 0.0)


def _is_finite(value: float) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


@dataclass(frozen=True)
class BSEuropeanPriceV1:
    price_per_unit: float
    pv_domestic: float


def price_european_option_bs_v1(
    *,
    spot: float,
    strike: float,
    domestic_df: float,
    foreign_df: float,
    vol: float,
    ttm_years: float,
    option_type: str,
    notional: float,
    time_fraction_policy_id: str,
) -> BSEuropeanPriceV1:
    if time_fraction_policy_id != TIME_FRACTION_POLICY_ACT_365F:
        raise ValueError(
            f"time_fraction_policy_id must be {TIME_FRACTION_POLICY_ACT_365F}"
        )

    if not _is_finite(spot) or float(spot) <= 0.0:
        raise ValueError("spot must be finite and > 0")
    if not _is_finite(strike) or float(strike) <= 0.0:
        raise ValueError("strike must be finite and > 0")
    if not _is_finite(domestic_df) or float(domestic_df) <= 0.0:
        raise ValueError("domestic_df must be finite and > 0")
    if not _is_finite(foreign_df) or float(foreign_df) <= 0.0:
        raise ValueError("foreign_df must be finite and > 0")
    if not _is_finite(notional) or float(notional) <= 0.0:
        raise ValueError("notional must be finite and > 0")

    time_floor = _tol_abs(MetricClass.TIME)
    vol_floor = _tol_abs(MetricClass.VOL)

    if not _is_finite(ttm_years):
        raise ValueError("ttm_years must be finite")
    if float(ttm_years) < -time_floor:
        raise ValueError("ttm_years must be >= 0")

    if not _is_finite(vol):
        raise ValueError("vol must be finite")
    if float(vol) < -vol_floor:
        raise ValueError("vol must be >= 0")

    t = 0.0 if abs(float(ttm_years)) <= time_floor else float(ttm_years)
    sigma = 0.0 if abs(float(vol)) <= vol_floor else float(vol)

    opt = str(option_type).strip().lower()
    if opt not in {"call", "put"}:
        raise ValueError("option_type must be 'call' or 'put'")

    if t == 0.0:
        rate = 0.0
        div = 0.0
    else:
        rate = -math.log(float(domestic_df)) / t
        div = -math.log(float(foreign_df)) / t

    price_per_unit = float(
        bs_price(
            option_type=opt,
            spot=float(spot),
            strike=float(strike),
            rate=rate,
            div=div,
            vol=sigma,
            t=t,
        )
    )
    pv_domestic = float(price_per_unit * float(notional))

    return BSEuropeanPriceV1(price_per_unit=price_per_unit, pv_domestic=pv_domestic)


__all__ = [
    "BSEuropeanPriceV1",
    "TIME_FRACTION_POLICY_ACT_365F",
    "price_european_option_bs_v1",
]
