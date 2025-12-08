# core/services/strategy_planner_service.py
from __future__ import annotations

from typing import List

from api.schemas.strategy import (
    StrategySuggestRequest,
    StrategySuggestion,
    StrategyLeg,
    PayoffSummary,
)


def _build_base_strikes(req: StrategySuggestRequest) -> tuple[float, float, float]:
    spot = req.market.spot
    horizon_factor = max(0.05, min(req.goals.time_horizon_days / 365 * 0.3, 0.4))
    low_strike = spot * (1 - horizon_factor)
    high_strike = spot * (1 + horizon_factor)
    return spot, low_strike, high_strike


def _covered_call(req: StrategySuggestRequest) -> StrategySuggestion:
    spot, _, high = _build_base_strikes(req)
    expiry = req.market.expiry

    call_strike = high

    legs = [
        StrategyLeg(
            side="long",
            cp="CALL",
            strike=0.0,  # placeholder לנכס בסיס
            quantity=100,
            expiry=expiry,
        ),
        StrategyLeg(
            side="short",
            cp="CALL",
            strike=call_strike,
            quantity=100,
            expiry=expiry,
        ),
    ]

    payoff = PayoffSummary(
        max_profit=None,
        max_loss=None,
        breakeven_low=None,
        breakeven_high=call_strike,
    )

    tokens = [
        "אסטרטגיה סמי-שמרנית למשקיע שכבר מחזיק את הנכס.",
        "מתאימה ליצירת הכנסה שוטפת מפרמיות.",
    ]

    risk_score = 0.3 if req.goals.risk_tolerance == "low" else 0.4

    return StrategySuggestion(
        name="Covered Call",
        subtype="income/bullish-moderate",
        legs=legs,
        payoff_summary=payoff,
        risk_score=risk_score,
        explanation_tokens=tokens,
    )


def _bull_call_spread(req: StrategySuggestRequest) -> StrategySuggestion:
    spot, _, high = _build_base_strikes(req)
    expiry = req.market.expiry

    k1 = spot
    k2 = high

    legs = [
        StrategyLeg(side="long", cp="CALL", strike=k1, quantity=1, expiry=expiry),
        StrategyLeg(side="short", cp="CALL", strike=k2, quantity=1, expiry=expiry),
    ]

    payoff = PayoffSummary()

    tokens = [
        "חשיפה לעלייה מוגבלת בעלות נמוכה יותר מקניית CALL בודד.",
    ]

    risk_score = 0.4 if req.goals.risk_tolerance == "low" else 0.55

    return StrategySuggestion(
        name="Bull Call Spread",
        subtype="vertical/bullish",
        legs=legs,
        payoff_summary=payoff,
        risk_score=risk_score,
        explanation_tokens=tokens,
    )


def _bear_put_spread(req: StrategySuggestRequest) -> StrategySuggestion:
    spot, low, _ = _build_base_strikes(req)
    expiry = req.market.expiry

    k1 = spot
    k2 = low

    legs = [
        StrategyLeg(side="long", cp="PUT", strike=k1, quantity=1, expiry=expiry),
        StrategyLeg(side="short", cp="PUT", strike=k2, quantity=1, expiry=expiry),
    ]

    payoff = PayoffSummary()
    tokens = ["הגנה/הימור על ירידה עם עלות מוגבלת."]

    risk_score = 0.45 if req.goals.risk_tolerance == "low" else 0.6

    return StrategySuggestion(
        name="Bear Put Spread",
        subtype="vertical/bearish",
        legs=legs,
        payoff_summary=payoff,
        risk_score=risk_score,
        explanation_tokens=tokens,
    )


def _iron_condor(req: StrategySuggestRequest) -> StrategySuggestion:
    spot, low, high = _build_base_strikes(req)
    expiry = req.market.expiry

    width = (high - low) / 4
    k_put_short = spot - width
    k_put_long = k_put_short - width
    k_call_short = spot + width
    k_call_long = k_call_short + width

    legs = [
        StrategyLeg(
            side="short", cp="PUT", strike=k_put_short, quantity=1, expiry=expiry
        ),
        StrategyLeg(
            side="long", cp="PUT", strike=k_put_long, quantity=1, expiry=expiry
        ),
        StrategyLeg(
            side="short", cp="CALL", strike=k_call_short, quantity=1, expiry=expiry
        ),
        StrategyLeg(
            side="long", cp="CALL", strike=k_call_long, quantity=1, expiry=expiry
        ),
    ]

    payoff = PayoffSummary()
    tokens = [
        "אסטרטגיה קלאסית לשוק צדדי (range).",
        "הפסד מקסימלי מוגבל לשני הצדדים, הכנסה מפרמיה מראש.",
    ]

    risk_score = 0.6 if req.goals.risk_tolerance == "medium" else 0.75

    return StrategySuggestion(
        name="Iron Condor",
        subtype="income/range-trading",
        legs=legs,
        payoff_summary=payoff,
        risk_score=risk_score,
        explanation_tokens=tokens,
    )


def suggest_strategies_service(req: StrategySuggestRequest) -> List[StrategySuggestion]:
    """מנוע Planner היוריסטי ל-V2."""
    suggestions: List[StrategySuggestion] = []

    view = req.goals.view
    risk = req.goals.risk_tolerance

    if view == "bullish":
        suggestions.append(_bull_call_spread(req))
        if risk in ("medium", "high"):
            suggestions.append(_covered_call(req))
    elif view == "bearish":
        suggestions.append(_bear_put_spread(req))
    elif view in ("neutral", "range"):
        suggestions.append(_iron_condor(req))
        if risk == "low":
            suggestions.append(_covered_call(req))
    else:
        suggestions.append(_covered_call(req))
        suggestions.append(_iron_condor(req))

    return suggestions
