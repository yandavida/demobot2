# core/services/fx_service.py
from __future__ import annotations

from typing import List, Dict, Any

from api.schemas.fx import (
    FxForwardRequest,
    FxCurvePoint,
    FxPlSummary,
    FxRiskProfile,
    FxScenarioResult,
)


def analyze_fx_forward_service(req: FxForwardRequest) -> Dict[str, Any]:
    """
    מנוע חישוב בסיסי לעסקת FX Forward אחת.

    לוגיקה:
    - BUY base:  P/L = (S_T - K) * Notional
    - SELL base: P/L = (K - S_T) * Notional

    מחזיר dict בפורמט שניתן למפות ישירות ל-FxForwardResponse.
    """

    # ------------------------------
    # בניית עקום מחירים סביב ה-spot
    # ------------------------------
    if req.curve_points < 11 or req.curve_points > 501:
        raise ValueError("curve_points must be between 11 and 501")

    step = (req.curve_max_pct - req.curve_min_pct) / (req.curve_points - 1)

    curve: List[FxCurvePoint] = []
    pl_values: List[float] = []

    direction_sign = 1.0 if req.direction == "BUY" else -1.0

    for i in range(req.curve_points):
        pct_move = req.curve_min_pct + i * step
        s_t = req.spot * (1.0 + pct_move)

        pl = direction_sign * (s_t - req.forward_rate) * req.notional
        curve.append(FxCurvePoint(underlying=s_t, pl=pl))
        pl_values.append(pl)

    if not pl_values:
        raise RuntimeError("Failed to build P&L curve")

    # ------------------------------
    # סיכום P&L בסיסי
    # ------------------------------
    pl_at_spot = direction_sign * (req.spot - req.forward_rate) * req.notional
    pl_at_forward = 0.0  # בפקיעה בשער החוזה – תיאורטית 0

    max_profit = max(pl_values)
    max_loss = min(pl_values)

    pl_summary = FxPlSummary(
        max_profit=max_profit,
        max_loss=max_loss,
        expected_pl=None,
        pl_at_spot=pl_at_spot,
        pl_at_forward=pl_at_forward,
    )

    # ------------------------------
    # פרופיל סיכון בסיסי
    # ------------------------------
    notional_value_quote = req.spot * req.notional
    loss_ratio = 0.0
    if notional_value_quote > 0:
        loss_ratio = abs(max_loss) / notional_value_quote

    if loss_ratio < 0.05:
        risk_level = "Low"
    elif loss_ratio < 0.15:
        risk_level = "Medium"
    else:
        risk_level = "High"

    risk_profile = FxRiskProfile(
        risk_level=risk_level,
        risk_score=min(loss_ratio, 1.0),
        tags=[risk_level],
        comments=[
            f"Max loss ≈ {loss_ratio:.2%} מהנומינלי (base*spot).",
            "מודל סיכון בסיסי ל-V2 – ניתן לשיפור בהמשך.",
        ],
    )

    # ------------------------------
    # תרחישים לדוגמה
    # ------------------------------
    scenarios: List[FxScenarioResult] = []

    for name, pct in [
        ("Spot -5%", -0.05),
        ("Spot", 0.0),
        ("Spot +5%", 0.05),
    ]:
        s_t = req.spot * (1.0 + pct)
        pl = direction_sign * (s_t - req.forward_rate) * req.notional
        scenarios.append(
            FxScenarioResult(
                name=name,
                description=f"תרחיש {name} על שער ה-Spot.",
                pl=pl,
                probability=None,
            )
        )

    # נחזיר dict פשוט – ה-router יעשה ממנו ResponseModel
    return {
        "curve": [c.dict() for c in curve],
        "pl_summary": pl_summary.dict(),
        "risk_profile": risk_profile.dict(),
        "scenarios": [s.dict() for s in scenarios],
    }
