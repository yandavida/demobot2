# Layer: core_math
# core/fx_math.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Dict, Any

import numpy as np
import pandas as pd

Side = Literal["buy", "sell"]  # buy = long base, sell = short base


@dataclass
class FxDealInput:
    """
    מודל בסיסי לעסקת FX אחת (למשל Forward פשוט).
    pair: צמד מטבעות – למשל "EURUSD"
    notional: נומינלי במטבע הבסיס (EUR בעבור EURUSD)
    direction: buy/sell base
    forward_rate: השער שסוכם בחוזה (forward)
    spot_today: השער הנוכחי בשוק
    maturity_days: זמן לפקיעה (רק למידע / הצגה כרגע)
    """

    pair: str
    notional: float
    direction: Side
    forward_rate: float
    spot_today: float
    maturity_days: int = 30


def fx_forward_payoff_curve(
    deal: FxDealInput,
    moves: np.ndarray | None = None,
) -> pd.DataFrame:
    """
    מחשב עקומת P/L לעסקת Forward אחת, במטבע ה-quote.

    moves: וקטור של שינויי מחיר באחוזים סביב spot (למשל [-0.1 ... 0.1]).
    אם לא סופק – נשתמש בטווח ברירת מחדל של -10% עד +10%.
    """
    if moves is None:
        moves = np.linspace(-0.10, 0.10, 51)  # מ- -10% עד +10%

    # מחירי Spot אפשריים
    spot_scenarios = deal.spot_today * (1.0 + moves)

    # סימן: buy base = מרוויח כשה-spot עולה יחסית ל-forward
    direction_sign = 1.0 if deal.direction == "buy" else -1.0

    # P/L במטבע ה-quote (למשל USD בעבור EURUSD)
    pl_quote = direction_sign * deal.notional * (spot_scenarios - deal.forward_rate)

    df = pd.DataFrame(
        {
            "pair": deal.pair,
            "spot": spot_scenarios,
            "move_pct": moves * 100.0,
            "pl_quote": pl_quote,
        }
    )
    return df


def summarize_fx_pl(
    deal: FxDealInput,
    curve_df: pd.DataFrame,
) -> Dict[str, Any]:
    """
    מסכם מדדים בסיסיים לעסקת FX:
    - pl_at_spot (P/L לפי spot_today)
    - max_profit / max_loss
    - notional_value_quote (קירוב להון שבסיכון)
    """
    if curve_df.empty:
        return {
            "pl_at_spot": 0.0,
            "max_profit": 0.0,
            "max_loss": 0.0,
            "notional_value_quote": 0.0,
        }

    # למצוא את הנקודה הקרובה ל-spot_today
    idx_spot = (curve_df["spot"] - deal.spot_today).abs().idxmin()
    pl_at_spot = float(curve_df.loc[idx_spot, "pl_quote"])

    max_profit = float(curve_df["pl_quote"].max())
    max_loss = float(curve_df["pl_quote"].min())

    # הערכת הון שבסיכון (נומינלי * spot)
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
    }
    return summary
