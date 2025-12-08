# Layer: strategies
# core/strategy_builders/volatility_builders.py
from __future__ import annotations

from typing import Sequence, List

import pandas as pd

from core.models import Leg, Position

from core.strategy_builders.basic_builders import _closest_strike


class StraddleBuilder:
    """
    Long Straddle – קנייה של CALL+PUT באותו סטרייק (ATM).
    מתאים במיוחד כש"השוק זז הרבה (תנודתי)" בלי כיוון מוגדר.
    """

    id: str = "long_straddle_basic"
    name: str = "Long Straddle (קניית תנודתיות)"

    def build(
        self,
        inputs: RecommendationInputs,
        df_chain: pd.DataFrame | None = None,
    ) -> Sequence[StrategyCandidate]:
        # אם המשתמש לא ציין explicitly שוק תנודתי – לא מציעים Straddle
        if inputs.market_view != "השוק זז הרבה (תנודתי)":
            return []

        spot = inputs.spot

        # ננסה למצוא סטרייק ATM אמיתי מהשרשרת, אם קיימת
        if df_chain is not None and not df_chain.empty:
            strikes = sorted(df_chain["strike"].unique().tolist())
            atm_strike = _closest_strike(strikes, spot)

            def _mid_price(cp: str, strike: float) -> float:
                sub = df_chain[(df_chain["cp"] == cp) & (df_chain["strike"] == strike)]
                if "price" in sub.columns and not sub.empty:
                    return float(sub["price"].iloc[0])
                return 5.0  # דיפולט גס

            call_prem = _mid_price("CALL", atm_strike)
            put_prem = _mid_price("PUT", atm_strike)
        else:
            # בלי שרשרת – סימולציה סביב הספוט
            atm_strike = spot
            # פרמיות דיפולטיביות – רק כדי לקבל payoff סביר
            call_prem = 5.0
            put_prem = 5.0

        legs: List[Leg] = [
            Leg(
                side="long", cp="CALL", strike=atm_strike, quantity=1, premium=call_prem
            ),
            Leg(side="long", cp="PUT", strike=atm_strike, quantity=1, premium=put_prem),
        ]
        position = Position(legs=legs)

        candidate = StrategyCandidate(
            position=position,
            name=self.name,
            subtype="Long Volatility, Gamma/Vega חיובי",
            description=(
                "קניית CALL+PUT באותו סטרייק (לרוב סביב ה-ATM). "
                "ההפסד מוגבל לדביט ההתחלתי, והרווח פתוח אם השוק זז חזק "
                "למעלה או למטה."
            ),
            tags=["long-vol", "gamma+", "vega+", "event"],
        )
        return [candidate]


class StrangleBuilder:
    """
    Long Strangle – קניית PUT מתחת למחיר ו-CALL מעל המחיר.
    נותן אקספוזר לתנודתיות, עם דביט מעט קטן יותר מ-Straddle.
    """

    id: str = "long_strangle_basic"
    name: str = "Long Strangle (קניית תנודתיות זולה יותר)"

    def build(
        self,
        inputs: RecommendationInputs,
        df_chain: pd.DataFrame | None = None,
    ) -> Sequence[StrategyCandidate]:
        # גם פה – מתאים כשמחפשים תנודתיות
        if inputs.market_view != "השוק זז הרבה (תנודתי)":
            return []

        spot = inputs.spot

        # מרחק סטרייקים לפי אגרסיביות:
        # אגרסיבי → סטרייקים קרובים (דביט גבוה, סיכוי גבוה לזוז לטווח),
        # שמרני → סטרייקים רחוקים יותר (דביט נמוך יותר).
        if inputs.aggressiveness <= 3:
            pct = 0.10  # שמרני – ±10%
        elif inputs.aggressiveness <= 6:
            pct = 0.07  # בינוני – ±7%
        else:
            pct = 0.05  # אגרסיבי – ±5%

        if df_chain is not None and not df_chain.empty:
            strikes = sorted(df_chain["strike"].unique().tolist())
            put_target = spot * (1.0 - pct)
            call_target = spot * (1.0 + pct)

            put_strike = _closest_strike(strikes, put_target)
            call_strike = _closest_strike(strikes, call_target)

            def _mid_price(cp: str, strike: float) -> float:
                sub = df_chain[(df_chain["cp"] == cp) & (df_chain["strike"] == strike)]
                if "price" in sub.columns and not sub.empty:
                    return float(sub["price"].iloc[0])
                return 3.0

            put_prem = _mid_price("PUT", put_strike)
            call_prem = _mid_price("CALL", call_strike)
        else:
            # בלי שרשרת – סימולציה סביב הספוט
            put_strike = spot * (1.0 - pct)
            call_strike = spot * (1.0 + pct)
            put_prem = 3.0
            call_prem = 3.0

        legs: List[Leg] = [
            Leg(side="long", cp="PUT", strike=put_strike, quantity=1, premium=put_prem),
            Leg(
                side="long",
                cp="CALL",
                strike=call_strike,
                quantity=1,
                premium=call_prem,
            ),
        ]
        position = Position(legs=legs)

        candidate = StrategyCandidate(
            position=position,
            name=self.name,
            subtype="Long Vol, OTM",
            description=(
                "קניית PUT מתחת למחיר ו-CALL מעל המחיר (OTM). "
                "ההפסד מוגבל לדביט הכולל, והרווח פתוח בתנועה חדה "
                "כלפי מעלה או מטה. לרוב דביט נמוך יותר מ-Straddle."
            ),
            tags=["long-vol", "gamma+", "vega+", "otm"],
        )
        return [candidate]
