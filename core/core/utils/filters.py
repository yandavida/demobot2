# Layer: utils
from __future__ import annotations
import pandas as pd


def df_basic_filter(
    df: pd.DataFrame,
    strikes_range: tuple[float, float],
    cp_sel: list[str],
) -> pd.DataFrame:
    lo, hi = strikes_range
    mask_strike = (df["strike"] >= lo) & (df["strike"] <= hi)
    mask_cp = df["cp"].isin(cp_sel) if cp_sel else True
    return df.loc[mask_strike & mask_cp].reset_index(drop=True)


def apply_advanced_filters(
    df: pd.DataFrame,
    price_range: tuple[float, float] | None,
    delta_range: tuple[float, float] | None,
    gamma_range: tuple[float, float] | None,
    theta_range: tuple[float, float] | None,
    vega_range: tuple[float, float] | None,
    rho_range: tuple[float, float] | None,
) -> pd.DataFrame:
    out = df.copy()
    if price_range:
        out = out[(out["price"] >= price_range[0]) & (out["price"] <= price_range[1])]
    if delta_range:
        out = out[(out["delta"] >= delta_range[0]) & (out["delta"] <= delta_range[1])]
    if gamma_range:
        out = out[(out["gamma"] >= gamma_range[0]) & (out["gamma"] <= gamma_range[1])]
    if theta_range:
        out = out[(out["theta"] >= theta_range[0]) & (out["theta"] <= theta_range[1])]
    if vega_range:
        out = out[(out["vega"] >= vega_range[0]) & (out["vega"] <= vega_range[1])]
    if rho_range:
        out = out[(out["rho"] >= rho_range[0]) & (out["rho"] <= rho_range[1])]
    return out.reset_index(drop=True)
