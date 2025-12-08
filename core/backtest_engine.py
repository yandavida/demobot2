# core/backtest_engine.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd

from core.models import Position
from core.payoff import summarize_position_pl, payoff_position
from core.greeks import calc_position_greeks
from core.risk_engine import classify_risk_level
from core.strategy_warnings import get_position_warnings


@dataclass
class BacktestConfig:
    """הגדרות חישוב לבקטסט יחיד על פוזיציה."""

    position: Position
    spot: float
    lower_factor: float
    upper_factor: float
    num_points: int
    dte_days: int
    iv: float  # כבר ביחס (0.2 ולא 20)
    r: float
    q: float
    contract_multiplier: int


@dataclass
class BacktestResult:
    """תוצאה עשירה של בקטסט – אבל בפועל אנחנו מחזירים dict להמשך נוח ב-UI."""

    curve_df: pd.DataFrame
    break_even_points: List[float]
    scenarios_df: pd.DataFrame
    pl_summary: Dict[str, Any]
    greeks: Dict[str, float]
    risk: Dict[str, Any]


def _pl_at_spot(curve_df: pd.DataFrame, spot: float) -> float:
    """P/L בנקודת ה-Spot מתוך עקומת P/L מלאה."""
    if curve_df.empty:
        return 0.0
    idx = (curve_df["price"] - spot).abs().idxmin()
    return float(curve_df.loc[idx, "pl"])


def run_full_backtest(position: Position, cfg: BacktestConfig) -> Dict[str, Any]:
    """
    מנוע בקטסט יחיד:
    - מחשב עקומת P/L מלאה (כולל מכפיל)
    - תרחישי מחיר
    - Greeks
    - סיכומי רווח/הפסד באחוזים
    - פרופיל סיכון כולל אזהרות
    מחזיר dict עם כל הנתונים שה-UI צריך.
    """
    # -------- עקומת P/L בסיסית (ליחידה אחת) --------
    summary = summarize_position_pl(
        position=position,
        center_price=cfg.spot,
        lower_factor=cfg.lower_factor,
        upper_factor=cfg.upper_factor,
        num_points=cfg.num_points,
    )

    curve_df: pd.DataFrame = summary["curve_df"]  # type: ignore[assignment]
    max_profit_unit: float = summary["max_profit"]  # type: ignore[assignment]
    max_loss_unit: float = summary["max_loss"]  # type: ignore[assignment]
    break_even_points: list[float] = summary["break_even_points"]  # type: ignore[assignment]

    # -------- התאמה למכפיל חוזה --------
    curve_df_full = curve_df.copy()
    curve_df_full["pl"] *= cfg.contract_multiplier
    max_profit = max_profit_unit * cfg.contract_multiplier
    max_loss = max_loss_unit * cfg.contract_multiplier

    pl_at_spot = _pl_at_spot(curve_df_full, cfg.spot)

    # -------- חישוב הון מושקע ורווח/הפסד באחוזים --------
    if max_loss < 0:
        invested_capital = abs(max_loss)
    else:
        invested_capital = abs(max_profit) if max_profit != 0 else 0.0

    if invested_capital > 0:
        max_profit_pct = (max_profit / invested_capital) * 100
        max_loss_pct = (max_loss / invested_capital) * 100
        pl_spot_pct = (pl_at_spot / invested_capital) * 100
    else:
        max_profit_pct = max_loss_pct = pl_spot_pct = 0.0

    rr_ratio = abs(max_profit / max_loss) if max_loss != 0 else None

    pl_summary: Dict[str, Any] = {
        "invested_capital": invested_capital,
        "max_profit": max_profit,
        "max_loss": max_loss,
        "max_profit_pct": max_profit_pct,
        "max_loss_pct": max_loss_pct,
        "pl_at_spot": pl_at_spot,
        "pl_spot_pct": pl_spot_pct,
        "rr_ratio": rr_ratio,
    }

    # -------- Greeks (Black–Scholes) --------
    greeks_obj = calc_position_greeks(
        position=position,
        spot=cfg.spot,
        dte_days=cfg.dte_days,
        r=cfg.r,
        q=cfg.q,
        iv=cfg.iv,
        multiplier=cfg.contract_multiplier,
    )

    greeks: Dict[str, float] = {
        "delta": greeks_obj.delta,
        "gamma": greeks_obj.gamma,
        "vega": greeks_obj.vega,
        "theta": greeks_obj.theta,
        "rho": greeks_obj.rho,
    }

    # -------- פרופיל סיכון כולל אזהרות --------
    risk_level, risk_comment = classify_risk_level(
        max_loss=max_loss,
        invested_capital=invested_capital,
        pos_greeks=greeks_obj,
    )

    warnings = get_position_warnings(
        position=position,
        spot=cfg.spot,
        greeks=greeks_obj,
        be_prices=break_even_points,
    )

    risk: Dict[str, Any] = {
        "level": risk_level,
        "comment": risk_comment,
        "warnings": warnings,
    }

    # -------- תרחישי מחיר (בבקסטט) --------
    moves_pct = [-0.10, -0.05, -0.02, 0.0, 0.02, 0.05, 0.10]
    rows: list[Dict[str, Any]] = []

    for m in moves_pct:
        price = cfg.spot * (1.0 + m)
        pl_unit = payoff_position(position, price)
        pl_full = pl_unit * cfg.contract_multiplier

        g_m = calc_position_greeks(
            position=position,
            spot=price,
            dte_days=cfg.dte_days,
            r=cfg.r,
            q=cfg.q,
            iv=cfg.iv,
            multiplier=cfg.contract_multiplier,
        )

        rows.append(
            {
                "Move %": m * 100.0,
                "Spot price": price,
                "P/L at expiry": pl_full,
                "Delta (BS)": g_m.delta,
            }
        )

    scenarios_df = pd.DataFrame(rows)

    # אפשר גם להחזיר BacktestResult, אבל ל-UI נוח לקבל dict
    return {
        "curve_df": curve_df_full,
        "break_even_points": break_even_points,
        "scenarios_df": scenarios_df,
        "pl_summary": pl_summary,
        "greeks": greeks,
        "risk": risk,
    }
