# Layer: strategies
# core/strategy_builders/basic_builders.py
from __future__ import annotations

from typing import Sequence, List

import pandas as pd

from core.models import Leg, Position


# ===== עזר פנימי – בניית פוזיציות בסיס =====


def _build_iron_condor_around_spot(
    spot: float,
    inner_pct: float,
    outer_pct: float,
    qty: int = 1,
    short_premium: float = 4.0,
    long_premium: float = 2.0,
) -> Position:
    """
    בונה Iron Condor סימטרי סביב המחיר (ללא תלות בשרשרת אמיתית).
    """
    put_short_strike = spot * (1.0 - inner_pct)
    put_long_strike = spot * (1.0 - outer_pct)
    call_short_strike = spot * (1.0 + inner_pct)
    call_long_strike = spot * (1.0 + outer_pct)

    legs: List[Leg] = [
        Leg(
            side="short",
            cp="PUT",
            strike=put_short_strike,
            quantity=qty,
            premium=short_premium,
        ),
        Leg(
            side="long",
            cp="PUT",
            strike=put_long_strike,
            quantity=qty,
            premium=long_premium,
        ),
        Leg(
            side="short",
            cp="CALL",
            strike=call_short_strike,
            quantity=qty,
            premium=short_premium,
        ),
        Leg(
            side="long",
            cp="CALL",
            strike=call_long_strike,
            quantity=qty,
            premium=long_premium,
        ),
    ]
    return Position(legs=legs)


def _build_put_credit_spread_synthetic(
    spot: float,
    inner_pct: float,
    outer_pct: float,
    qty: int = 1,
    short_premium: float = 4.0,
    long_premium: float = 2.0,
) -> Position:
    """
    בונה Put Credit Spread “סינתטי” (בלי שרשרת).
    """
    put_short_strike = spot * (1.0 - inner_pct)
    put_long_strike = spot * (1.0 - outer_pct)

    legs: List[Leg] = [
        Leg(
            side="short",
            cp="PUT",
            strike=put_short_strike,
            quantity=qty,
            premium=short_premium,
        ),
        Leg(
            side="long",
            cp="PUT",
            strike=put_long_strike,
            quantity=qty,
            premium=long_premium,
        ),
    ]
    return Position(legs=legs)


def _closest_strike(strikes: list[float], target: float) -> float:
    if not strikes:
        return target
    return min(strikes, key=lambda k: abs(k - target))


# ===== מחלקות אסטרטגיה – מממשות StrategyBuilder =====


class IronCondorBuilder:
    """
    בונה Iron Condor ניטרלי סביב הספוט – שמרני / אגרסיבי לפי aggressiveness.
    """

    id: str = "iron_condor_basic"
    name: str = "Iron Condor סביב המחיר"

    def build(
        self,
        inputs: RecommendationInputs,
        df_chain: pd.DataFrame | None = None,
    ) -> Sequence[StrategyCandidate]:
        spot = inputs.spot

        # פרופיל מרחק סטרייקים לפי אגרסיביות
        if inputs.aggressiveness <= 3:
            inner_pct = 0.08
            outer_pct = 0.12
        elif inputs.aggressiveness <= 6:
            inner_pct = 0.05
            outer_pct = 0.09
        else:
            inner_pct = 0.03
            outer_pct = 0.06

        # ניסיון להשתמש בשרשרת אמיתית אם קיימת
        if df_chain is not None and not df_chain.empty:
            put_strikes = sorted(
                df_chain.loc[df_chain["cp"] == "PUT", "strike"].unique().tolist()
            )
            call_strikes = sorted(
                df_chain.loc[df_chain["cp"] == "CALL", "strike"].unique().tolist()
            )

            target_put_short = spot * (1.0 - inner_pct)
            target_put_long = spot * (1.0 - outer_pct)
            target_call_short = spot * (1.0 + inner_pct)
            target_call_long = spot * (1.0 + outer_pct)

            put_short_strike = _closest_strike(put_strikes, target_put_short)
            put_long_strike = _closest_strike(put_strikes, target_put_long)
            call_short_strike = _closest_strike(call_strikes, target_call_short)
            call_long_strike = _closest_strike(call_strikes, target_call_long)

            def _mid_price(cp: str, strike: float) -> float:
                sub = df_chain[(df_chain["cp"] == cp) & (df_chain["strike"] == strike)]
                if "price" in sub.columns and not sub.empty:
                    return float(sub["price"].iloc[0])
                return 3.0  # דיפולט גס

            legs: list[Leg] = [
                Leg(
                    side="short",
                    cp="PUT",
                    strike=put_short_strike,
                    quantity=1,
                    premium=_mid_price("PUT", put_short_strike),
                ),
                Leg(
                    side="long",
                    cp="PUT",
                    strike=put_long_strike,
                    quantity=1,
                    premium=_mid_price("PUT", put_long_strike),
                ),
                Leg(
                    side="short",
                    cp="CALL",
                    strike=call_short_strike,
                    quantity=1,
                    premium=_mid_price("CALL", call_short_strike),
                ),
                Leg(
                    side="long",
                    cp="CALL",
                    strike=call_long_strike,
                    quantity=1,
                    premium=_mid_price("CALL", call_long_strike),
                ),
            ]
            position = Position(legs=legs)
        else:
            # בלי שרשרת – סימולציה סביב המחיר
            position = _build_iron_condor_around_spot(
                spot=spot,
                inner_pct=inner_pct,
                outer_pct=outer_pct,
                qty=1,
            )

        candidate = StrategyCandidate(
            position=position,
            name=self.name,
            subtype="Credit, ניטרלי",
            description=(
                "איירון קונדור סימטרי סביב מחיר הנכס, המייצר קרדיט התחלתי "
                "ומרוויח כל עוד המחיר נשאר בטווח הסטרייקים הפנימיים."
            ),
            tags=["neutral", "income", "range"],
        )
        return [candidate]


class PutCreditSpreadBuilder:
    """
    בונה Put Credit Spread – מתאים להטיה שורית/נייטרלית.
    """

    id: str = "put_credit_spread_basic"
    name: str = "Put Credit Spread"

    def build(
        self,
        inputs: RecommendationInputs,
        df_chain: pd.DataFrame | None = None,
    ) -> Sequence[StrategyCandidate]:
        # אם המשתמש ציין שוק יורד חזק – פחות מתאים להמלצה הזו
        if inputs.market_view == "השוק צפוי לרדת":
            return []

        spot = inputs.spot

        if inputs.aggressiveness <= 3:
            inner_pct = 0.06
            outer_pct = 0.10
        elif inputs.aggressiveness <= 6:
            inner_pct = 0.05
            outer_pct = 0.08
        else:
            inner_pct = 0.03
            outer_pct = 0.06

        if df_chain is not None and not df_chain.empty:
            put_strikes = sorted(
                df_chain.loc[df_chain["cp"] == "PUT", "strike"].unique().tolist()
            )
            target_short = spot * (1.0 - inner_pct)
            target_long = spot * (1.0 - outer_pct)

            put_short_strike = _closest_strike(put_strikes, target_short)
            put_long_strike = _closest_strike(put_strikes, target_long)

            def _mid_price(cp: str, strike: float) -> float:
                sub = df_chain[(df_chain["cp"] == cp) & (df_chain["strike"] == strike)]
                if "price" in sub.columns and not sub.empty:
                    return float(sub["price"].iloc[0])
                return 3.0

            legs: list[Leg] = [
                Leg(
                    side="short",
                    cp="PUT",
                    strike=put_short_strike,
                    quantity=1,
                    premium=_mid_price("PUT", put_short_strike),
                ),
                Leg(
                    side="long",
                    cp="PUT",
                    strike=put_long_strike,
                    quantity=1,
                    premium=_mid_price("PUT", put_long_strike),
                ),
            ]
            position = Position(legs=legs)
        else:
            position = _build_put_credit_spread_synthetic(
                spot=spot,
                inner_pct=inner_pct,
                outer_pct=outer_pct,
                qty=1,
            )

        candidate = StrategyCandidate(
            position=position,
            name=self.name,
            subtype="Bullish credit",
            description=(
                "מכירת PUT קרוב למחיר וקניית PUT עמוק יותר מתחתיו להגבלת הסיכון. "
                "מתאים לשוק שורי-שמרני או נייטרלי מעט."
            ),
            tags=["bullish", "credit", "defined-risk"],
        )
        return [candidate]
