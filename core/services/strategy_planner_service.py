# core/services/strategy_planner_service.py
from __future__ import annotations

from typing import List, Any, Dict


def _build_base_strikes(req: Any) -> tuple[float, float, float]:
    spot = req.market.spot
    horizon_factor = max(0.05, min(req.goals.time_horizon_days / 365 * 0.3, 0.4))
    low_strike = spot * (1 - horizon_factor)
    high_strike = spot * (1 + horizon_factor)
    return spot, low_strike, high_strike


def _covered_call(req: Any) -> Dict[str, Any]:
    spot, _, high = _build_base_strikes(req)
    expiry = req.market.expiry

    call_strike = high

    legs = [
        {"side": "long", "cp": "CALL", "strike": 0.0, "quantity": 100, "expiry": expiry},
        {"side": "short", "cp": "CALL", "strike": call_strike, "quantity": 100, "expiry": expiry},
    ]

    payoff = {"max_profit": None, "max_loss": None, "breakeven_low": None, "breakeven_high": call_strike}

    tokens = [
        "אסטרטגיה סמי-שמרנית למשקיע שכבר מחזיק את הנכס.",
        "מתאימה ליצירת הכנסה שוטפת מפרמיות.",
    ]

    risk_score = 0.3 if req.goals.risk_tolerance == "low" else 0.4

    return {
        "name": "Covered Call",
        "subtype": "income/bullish-moderate",
        "legs": legs,
        "payoff_summary": payoff,
        "risk_score": risk_score,
        "explanation_tokens": tokens,
    }


def _bull_call_spread(req: Any) -> Dict[str, Any]:
    spot, _, high = _build_base_strikes(req)
    expiry = req.market.expiry

    k1 = spot
    k2 = high

    legs = [{"side": "long", "cp": "CALL", "strike": k1, "quantity": 1, "expiry": expiry}, {"side": "short", "cp": "CALL", "strike": k2, "quantity": 1, "expiry": expiry}]

    payoff = {}

    tokens = [
        "חשיפה לעלייה מוגבלת בעלות נמוכה יותר מקניית CALL בודד.",
    ]

    risk_score = 0.4 if req.goals.risk_tolerance == "low" else 0.55

    return {"name": "Bull Call Spread", "subtype": "vertical/bullish", "legs": legs, "payoff_summary": payoff, "risk_score": risk_score, "explanation_tokens": tokens}


def _bear_put_spread(req: Any) -> Dict[str, Any]:
    spot, low, _ = _build_base_strikes(req)
    expiry = req.market.expiry

    k1 = spot
    k2 = low

    legs = [{"side": "long", "cp": "PUT", "strike": k1, "quantity": 1, "expiry": expiry}, {"side": "short", "cp": "PUT", "strike": k2, "quantity": 1, "expiry": expiry}]

    payoff = {}
    tokens = ["הגנה/הימור על ירידה עם עלות מוגבלת."]

    risk_score = 0.45 if req.goals.risk_tolerance == "low" else 0.6

    return {"name": "Bear Put Spread", "subtype": "vertical/bearish", "legs": legs, "payoff_summary": payoff, "risk_score": risk_score, "explanation_tokens": tokens}


def _iron_condor(req: Any) -> Dict[str, Any]:
    spot, low, high = _build_base_strikes(req)
    expiry = req.market.expiry

    width = (high - low) / 4
    k_put_short = spot - width
    k_put_long = k_put_short - width
    k_call_short = spot + width
    k_call_long = k_call_short + width

    legs = [
        {"side": "short", "cp": "PUT", "strike": k_put_short, "quantity": 1, "expiry": expiry},
        {"side": "long", "cp": "PUT", "strike": k_put_long, "quantity": 1, "expiry": expiry},
        {"side": "short", "cp": "CALL", "strike": k_call_short, "quantity": 1, "expiry": expiry},
        {"side": "long", "cp": "CALL", "strike": k_call_long, "quantity": 1, "expiry": expiry},
    ]

    payoff = {}
    tokens = [
        "אסטרטגיה קלאסית לשוק צדדי (range).",
        "הפסד מקסימלי מוגבל לשני הצדדים, הכנסה מפרמיה מראש.",
    ]

    risk_score = 0.6 if req.goals.risk_tolerance == "medium" else 0.75

    return {"name": "Iron Condor", "subtype": "income/range-trading", "legs": legs, "payoff_summary": payoff, "risk_score": risk_score, "explanation_tokens": tokens}


def suggest_strategies_service(req: Any) -> List[Dict[str, Any]]:
    """מנוע Planner היוריסטי ל-V2."""
    suggestions: List[Dict[str, Any]] = []

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
