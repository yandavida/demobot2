from __future__ import annotations

import math

from core.market_data.market_snapshot_payload_v0 import MarketSnapshotPayloadV0
from core.numeric_policy import DEFAULT_TOLERANCES
from core.numeric_policy import MetricClass


class DfLookupError(KeyError):
    """Raised when required discount-factor inputs cannot be resolved."""


def _time_tol() -> float:
    return float(DEFAULT_TOLERANCES[MetricClass.TIME].abs or 0.0)


def _tenor_from_ttm(ttm_years: float) -> str:
    tol = _time_tol()
    if ttm_years < -tol:
        raise DfLookupError("ttm_years must be >= 0")
    if abs(ttm_years) <= tol:
        return "0D"

    days = int(round(ttm_years * 365.0))
    if days <= 0:
        raise DfLookupError("ttm_years must map to positive ACT/365 day tenor")

    reconstructed = days / 365.0
    if abs(reconstructed - ttm_years) > tol:
        raise DfLookupError("ttm_years must map exactly to ACT/365 day tenor (no interpolation)")

    return f"{days}D"


def _df_from_rate(rate: float, ttm_years: float, compounding: str) -> float:
    if ttm_years <= 0.0:
        return 1.0
    if compounding == "continuous":
        return float(math.exp(-float(rate) * float(ttm_years)))
    if compounding == "annual":
        return float((1.0 + float(rate)) ** (-float(ttm_years)))
    raise DfLookupError(f"unsupported compounding '{compounding}'")


def get_pair_dfs_v0(
    payload: MarketSnapshotPayloadV0,
    *,
    domestic_ccy: str,
    foreign_ccy: str,
    ttm_years: float,
) -> tuple[float, float]:
    tenor = _tenor_from_ttm(float(ttm_years))
    if tenor == "0D":
        return 1.0, 1.0

    dom = payload.curves.curves.get(domestic_ccy)
    if dom is None:
        raise DfLookupError(f"missing domestic currency rates for '{domestic_ccy}'")

    for_ = payload.curves.curves.get(foreign_ccy)
    if for_ is None:
        raise DfLookupError(f"missing foreign currency rates for '{foreign_ccy}'")

    if tenor not in dom.zero_rates:
        raise DfLookupError(f"missing domestic tenor '{tenor}' for '{domestic_ccy}'")
    if tenor not in for_.zero_rates:
        raise DfLookupError(f"missing foreign tenor '{tenor}' for '{foreign_ccy}'")

    r_dom = float(dom.zero_rates[tenor])
    r_for = float(for_.zero_rates[tenor])

    df_dom = _df_from_rate(r_dom, float(ttm_years), dom.compounding)
    df_for = _df_from_rate(r_for, float(ttm_years), for_.compounding)

    if not (df_dom > 0.0 and df_for > 0.0):
        raise DfLookupError("resolved discount factors must be > 0")

    return df_dom, df_for


__all__ = ["DfLookupError", "get_pair_dfs_v0"]
