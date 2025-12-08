# Layer: engine
# core/strategy_recommendations.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd

from core.models import Leg, Position
from core.payoff import summarize_position_pl


# ============================================================
#   מבני עזר
# ============================================================


@dataclass
class Goals:
    """פרופיל עסקה כפי שהוגדר בטופס."""

    target_profit_pct: float
    max_loss_pct: float
    dte: int
    aggressiveness: int  # 0–10
    market_view: str
    spot: float


@dataclass
class EngineContext:
    """קונטקסט פנימי למנוע – כדי לא להעביר מיליון פרמטרים לכל פונקציה."""

    goals: Goals
    contract_multiplier: int
    df_chain: Optional[pd.DataFrame]


# ============================================================
#   עזר כללי – בניית פוזיציות בסיסיות
# ============================================================


def _make_vertical_spread(
    spot: float,
    cp: str,
    credit: bool,
    width_pct: float,
    aggressiveness: int,
) -> Position:
    """
    בונה Vertical Spread פשוט (Credit / Debit) על בסיס ה-Spot.

    * cp: "CALL" / "PUT"
    * credit: True = Credit Spread, False = Debit
    * width_pct: רוחב בין הסטרייקים כאחוז מה-Spot (למשל 0.03 = 3%)
    """
    cp = cp.upper()
    assert cp in ("CALL", "PUT")

    # מרחק של הסטרייק הקרוב מה-Spot לפי אגרסיביות:
    # אגרסיבי → קרוב יחסית ל-Spot, שמרני → רחוק יותר
    agg_norm = max(0, min(10, aggressiveness))
    # 0 → 6%, 10 → 1%
    base_offset_pct = 0.06 - (agg_norm / 10.0) * 0.05

    if cp == "PUT":
        short_strike = spot * (1.0 - base_offset_pct)
        long_strike = short_strike - spot * width_pct
    else:  # CALL
        short_strike = spot * (1.0 + base_offset_pct)
        long_strike = short_strike + spot * width_pct

    # פרמיות – לא מדויקות, אבל נותנות צורה סבירה לגרף:
    # Credit: short = יקר יותר, long = זול יותר
    # Debit: להפך
    width = abs(long_strike - short_strike)
    base_premium = max(width * 0.25, 1.0)

    if credit:
        short_prem = base_premium * 1.2
        long_prem = base_premium * 0.6
        short_side = "short"
        long_side = "long"
    else:
        short_prem = base_premium * 0.6
        long_prem = base_premium * 1.2
        short_side = "long"
        long_side = "short"

    legs = [
        Leg(
            side=short_side, cp=cp, strike=short_strike, quantity=1, premium=short_prem
        ),
        Leg(side=long_side, cp=cp, strike=long_strike, quantity=1, premium=long_prem),
    ]
    return Position(legs=legs)


def _make_iron_condor(
    spot: float,
    width_inner_pct: float,
    width_outer_pct: float,
    aggressiveness: int,
) -> Position:
    """
    בונה Iron Condor על בסיס שני vertical credit spreads (PUT + CALL).
    """
    put_spread = _make_vertical_spread(
        spot=spot,
        cp="PUT",
        credit=True,
        width_pct=width_inner_pct,
        aggressiveness=aggressiveness,
    )
    call_spread = _make_vertical_spread(
        spot=spot,
        cp="CALL",
        credit=True,
        width_pct=width_inner_pct,
        aggressiveness=aggressiveness,
    )

    # נזיז את הרגליים הרחוקות עוד קצת החוצה כדי ליצור "כנפיים" רחבות יותר
    for leg in put_spread.legs:
        if leg.side == "long" and leg.cp == "PUT":
            leg.strike -= spot * (width_outer_pct - width_inner_pct)

    for leg in call_spread.legs:
        if leg.side == "long" and leg.cp == "CALL":
            leg.strike += spot * (width_outer_pct - width_inner_pct)

    return Position(legs=put_spread.legs + call_spread.legs)


def _make_long_strangle(
    spot: float,
    width_pct: float,
    aggressiveness: int,
) -> Position:
    """
    Long Strangle – קניית CALL מעל השוק ו-PUT מתחת לשוק.
    """
    agg_norm = max(0, min(10, aggressiveness))
    # כמה רחוק הסטרייקים יהיו – אגרסיבי → קרוב יותר
    offset_pct = 0.10 - (agg_norm / 10.0) * 0.06  # 10% → 4%

    put_strike = spot * (1.0 - offset_pct)
    call_strike = spot * (1.0 + offset_pct)

    width_put = spot * width_pct
    width_call = spot * width_pct

    put_prem = max(width_put * 0.35, 1.0)
    call_prem = max(width_call * 0.35, 1.0)

    legs = [
        Leg(side="long", cp="PUT", strike=put_strike, quantity=1, premium=put_prem),
        Leg(side="long", cp="CALL", strike=call_strike, quantity=1, premium=call_prem),
    ]
    return Position(legs=legs)


# ============================================================
#   פונקציית עזר – הפיכת Position ל-summary + הצעה
# ============================================================


def _build_suggestion(
    ctx: EngineContext,
    *,
    key: str,
    name: str,
    subtitle: str,
    description: str,
    position: Position,
) -> Optional[Dict[str, Any]]:
    """
    עוטפת Position ומחזירה מילון בפורמט שה-UI מצפה לו.
    אם יש שגיאה בסיכום ה-P/L – נחזיר None ונדלג.
    """
    try:
        summary = summarize_position_pl(
            position=position,
            center_price=ctx.goals.spot,
            lower_factor=0.7,
            upper_factor=1.3,
            num_points=201,
        )
    except Exception as e:
        # עדיף לא להפיל את כל המסך בגלל אסטרטגיה יחידה
        print(f"[strategy_recommendations] failed to summarize {key}: {e}")
        return None

    # אפשרות להוסיף בעתיד הון מושקע / capital_at_risk – כרגע נשאיר איכותי בלבד
    suggestion: Dict[str, Any] = {
        "key": key,
        "name": name,
        "subtitle": subtitle,
        "description": description,
        "position": position,
        "summary": summary,
    }
    return suggestion


# ============================================================
#   מנגנון בחירת האסטרטגיות (לוגיקה “חכמה”)
# ============================================================


def _classify_view(raw_view: str) -> str:
    """תרגום טקסט בעברית לקטגוריית שוק גסה."""
    if "כמעט לא זז" in raw_view:
        return "neutral"
    if "תנודתי" in raw_view:
        return "volatile"
    if "יעלה" in raw_view or "לעלות" in raw_view:
        return "bullish"
    if "ירד" in raw_view or "לרדת" in raw_view:
        return "bearish"
    return "neutral"


def _aggressiveness_band(agg: int) -> str:
    agg = max(0, min(10, agg))
    if agg <= 3:
        return "conservative"
    if agg <= 6:
        return "balanced"
    return "aggressive"


# ============================================================
#   API ראשי – מה שה-UI קורא
# ============================================================


def suggest_strategies_for_goals(
    *,
    target_profit_pct: float,
    max_loss_pct: float,
    dte: int,
    aggressiveness: int,
    market_view: str,
    spot: float,
    contract_multiplier: int = 100,
    df_chain: Optional[pd.DataFrame] = None,
) -> List[Dict[str, Any]]:
    """
    מנוע ההמלצות הראשי.

    מחזיר רשימת הצעות בפורמט:
    {
        "name": str,
        "subtitle": str,
        "description": str,
        "position": Position,
        "summary": dict  # summarize_position_pl(...)
    }
    """
    goals = Goals(
        target_profit_pct=float(target_profit_pct),
        max_loss_pct=float(max_loss_pct),
        dte=int(dte),
        aggressiveness=int(aggressiveness),
        market_view=market_view,
        spot=float(spot),
    )
    ctx = EngineContext(
        goals=goals,
        contract_multiplier=int(contract_multiplier),
        df_chain=df_chain,
    )

    view = _classify_view(goals.market_view)
    agg_band = _aggressiveness_band(goals.aggressiveness)

    suggestions: List[Dict[str, Any]] = []

    # --------------------------------------------------------
    # 1. Iron Condor – אסטרטגיה נייטרלית / תנודתית מתונה
    # --------------------------------------------------------
    if view in ("neutral", "volatile"):
        if agg_band == "conservative":
            inner = 0.05
            outer = 0.09
            subtitle = "איירון קונדור שמרני סביב מחיר הנכס – מרווח רחב"
        elif agg_band == "balanced":
            inner = 0.035
            outer = 0.07
            subtitle = "איירון קונדור מאוזן סביב מחיר הנכס"
        else:  # aggressive
            inner = 0.025
            outer = 0.05
            subtitle = "איירון קונדור אגרסיבי – סטרייקים קרובים יותר למחיר הנכס"

        ic_position = _make_iron_condor(
            spot=goals.spot,
            width_inner_pct=inner,
            width_outer_pct=outer,
            aggressiveness=goals.aggressiveness,
        )
        ic_desc = (
            "איירון קונדור בנוי מ-Put Credit Spread ו-Call Credit Spread. "
            "מתאים לשוק שנע בטווח צדדי, עם בקרת סיכון דרך רגליים קנויות."
        )
        sug = _build_suggestion(
            ctx,
            key="iron_condor",
            name="Iron Condor",
            subtitle=subtitle,
            description=ic_desc,
            position=ic_position,
        )
        if sug:
            suggestions.append(sug)

    # --------------------------------------------------------
    # 2. Put Credit Spread – שוק נייטרלי/עולה (Bullish to Neutral)
    # --------------------------------------------------------
    if view in ("neutral", "bullish"):
        if agg_band == "conservative":
            width = 0.03
            subtitle = "Put Credit Spread שמרני – סטרייק רחוק מה-Spot"
        elif agg_band == "balanced":
            width = 0.04
            subtitle = "Put Credit Spread מאוזן – הגנה סבירה על downside"
        else:
            width = 0.05
            subtitle = "Put Credit Spread אגרסיבי – קרוב יותר למחיר הנכס"

        pcs_position = _make_vertical_spread(
            spot=goals.spot,
            cp="PUT",
            credit=True,
            width_pct=width,
            aggressiveness=goals.aggressiveness,
        )
        pcs_desc = (
            "אסטרטגיית קרדיט על ידי מכירת PUT וקניית PUT רחוק יותר. "
            "מתאימה כאשר את מאמינה שהנכס לא ירד מתחת לאזור מסוים."
        )
        sug = _build_suggestion(
            ctx,
            key="put_credit_spread",
            name="Put Credit Spread",
            subtitle=subtitle,
            description=pcs_desc,
            position=pcs_position,
        )
        if sug:
            suggestions.append(sug)

    # --------------------------------------------------------
    # 3. Call Credit Spread – שוק נייטרלי/יורד (Bearish to Neutral)
    # --------------------------------------------------------
    if view in ("neutral", "bearish"):
        if agg_band == "conservative":
            width = 0.03
            subtitle = "Call Credit Spread שמרני – מעל ה-Spot עם מרווח רחב"
        elif agg_band == "balanced":
            width = 0.04
            subtitle = "Call Credit Spread מאוזן – מכסה עלייה מתונה"
        else:
            width = 0.05
            subtitle = "Call Credit Spread אגרסיבי – קרוב יחסית למחיר הנכס"

        ccs_position = _make_vertical_spread(
            spot=goals.spot,
            cp="CALL",
            credit=True,
            width_pct=width,
            aggressiveness=goals.aggressiveness,
        )
        ccs_desc = (
            "אסטרטגיית קרדיט על ידי מכירת CALL וקניית CALL רחוק יותר. "
            "מתאימה כאשר את חושבת שהנכס לא יעלה הרבה מעבר למחיר הנוכחי."
        )
        sug = _build_suggestion(
            ctx,
            key="call_credit_spread",
            name="Call Credit Spread",
            subtitle=subtitle,
            description=ccs_desc,
            position=ccs_position,
        )
        if sug:
            suggestions.append(sug)

    # --------------------------------------------------------
    # 4. Long Strangle – שוק תנודתי מאוד
    # --------------------------------------------------------
    if view == "volatile":
        if agg_band == "conservative":
            width = 0.02
            subtitle = "Long Strangle שמרני – סטרייקים רחוקים יותר מה-Spot"
        elif agg_band == "balanced":
            width = 0.03
            subtitle = "Long Strangle מאוזן – לוכד תנועה משמעותית למעלה או למטה"
        else:
            width = 0.035
            subtitle = "Long Strangle אגרסיבי – סטרייקים קרובים, רגישות גבוהה לתנועה"

        strangle_position = _make_long_strangle(
            spot=goals.spot,
            width_pct=width,
            aggressiveness=goals.aggressiveness,
        )
        strangle_desc = (
            "קניית CALL מעל השוק ו-PUT מתחת לשוק. "
            "מתאימה כאשר הציפייה היא לתנועה חזקה באחד הכיוונים, "
            "אבל ללא דעה ברורה לאן."
        )
        sug = _build_suggestion(
            ctx,
            key="long_strangle",
            name="Long Strangle",
            subtitle=subtitle,
            description=strangle_desc,
            position=strangle_position,
        )
        if sug:
            suggestions.append(sug)

    return suggestions


# ============================================================
#   כלי עזר ל-Builder – אין שינוי מה-API שהיה
# ============================================================


def position_to_legs_df(position: Position) -> pd.DataFrame:
    """
    המרה של Position ל-DataFrame לטאב ה-Builder.
    """
    rows = []
    for leg in position.legs:
        rows.append(
            {
                "side": leg.side,
                "cp": leg.cp,
                "strike": float(leg.strike),
                "quantity": int(getattr(leg, "quantity", 1)),
                "premium": float(leg.premium),
            }
        )
    return pd.DataFrame(rows)
