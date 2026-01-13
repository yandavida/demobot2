from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Dict, Any

# Layer: core_math
# core/fx_math.py

Side = Literal["buy", "sell"]  # buy = long base, sell = short base

@dataclass
class FxDealInput:
    pair: str
    notional: float
    direction: Side
    forward_rate: float
    spot_today: float
    maturity_days: int = 30

def fx_forward_payoff_curve(*args, **kwargs):
    """
    Adapter supporting:
      - fx_forward_payoff_curve(spot, forward, notional, side)
      - fx_forward_payoff_curve(deal=<FxDealInput>, moves=<iterable|None>)
    Returns deterministic payoff (float) או curve summary (dict) כמצופה.
    """
    if len(args) >= 4:
        spot, forward, notional, side = args[:4]
        if side.upper() == "BUY_BASE":
            return notional * (spot - forward)
        elif side.upper() == "SELL_BASE":
            return -notional * (spot - forward)
        else:
            raise ValueError(f"Invalid side: {side}")
    deal = args[0] if args else kwargs.get('deal')
    moves = args[1] if len(args) > 1 else kwargs.get('moves', None)
    import numpy as np
    if moves is None:
        moves = np.linspace(-0.10, 0.10, 51)
    spot_scenarios = deal.spot_today * (1.0 + moves)
    direction_sign = 1.0 if deal.direction == "buy" else -1.0
    pl_quote = direction_sign * deal.notional * (spot_scenarios - deal.forward_rate)
    curve = {
        "pair": deal.pair,
        "spot": spot_scenarios,
        "move_pct": moves * 100.0,
        "pl_quote": pl_quote,
    }
    idx_spot = (spot_scenarios - deal.spot_today).argmin()
    pl_at_spot = float(pl_quote[idx_spot])
    max_profit = float(pl_quote.max())
    max_loss = float(pl_quote.min())
    notional_value_quote = abs(deal.notional * deal.spot_today)
    summary: Dict[str, Any] = {
        "pl_at_spot": pl_at_spot,
        "max_profit": max_profit,
        "max_loss": max_loss,
        "notional_value_quote": notional_value_quote,
        "spot_today": deal.spot_today,
        "forward_rate": deal.forward_rate,
        "direction": deal.direction,
        "pair": deal.pair,
        "maturity_days": deal.maturity_days,
        "curve": curve,
    }
    return summary


def summarize_fx_pl(*args, **kwargs):
    """Backward-compatible alias used by higher layers."""
    return fx_forward_payoff_curve(*args, **kwargs)
