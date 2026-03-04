from __future__ import annotations

from dataclasses import dataclass
import math

from core.numeric_policy import DEFAULT_TOLERANCES
from core.numeric_policy import MetricClass
from core.services.scenario_risk_summary_v1 import ScenarioRiskSummaryV1


@dataclass(frozen=True)
class HedgeRecommendationV1:
    contract_version: str
    current_hedge_ratio: float
    target_worst_loss_domestic: float
    implied_worst_loss_unhedged_domestic: float
    recommended_hedge_ratio: float
    expected_worst_loss_domestic: float


def _tol_abs() -> float:
    return float(DEFAULT_TOLERANCES[MetricClass.PNL].abs or 0.0)


def _tol_rel() -> float:
    return float(DEFAULT_TOLERANCES[MetricClass.PNL].rel or 0.0)


def _clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def recommend_hedge_ratio_v1(
    risk_summary,
    *,
    current_hedge_ratio: float,
    target_worst_loss_domestic: float,
) -> HedgeRecommendationV1:
    if not isinstance(risk_summary, ScenarioRiskSummaryV1):
        raise ValueError("risk_summary must be ScenarioRiskSummaryV1")

    if not math.isfinite(current_hedge_ratio):
        raise ValueError("current_hedge_ratio must be finite")
    if not math.isfinite(target_worst_loss_domestic):
        raise ValueError("target_worst_loss_domestic must be finite")

    current_hedge_ratio = _clamp01(float(current_hedge_ratio))
    target = float(target_worst_loss_domestic)
    if target < 0.0:
        raise ValueError("target_worst_loss_domestic must be >= 0")

    current_worst_loss = abs(float(risk_summary.worst_loss_domestic))
    tol_abs = _tol_abs()
    tol_rel = _tol_rel()

    if math.isclose(current_hedge_ratio, 1.0, rel_tol=tol_rel, abs_tol=tol_abs) or current_hedge_ratio >= 1.0:
        return HedgeRecommendationV1(
            contract_version="v1",
            current_hedge_ratio=current_hedge_ratio,
            target_worst_loss_domestic=target,
            implied_worst_loss_unhedged_domestic=current_worst_loss,
            recommended_hedge_ratio=1.0,
            expected_worst_loss_domestic=0.0,
        )

    if target > current_worst_loss or math.isclose(target, current_worst_loss, rel_tol=tol_rel, abs_tol=tol_abs):
        unhedged_fraction = max(1.0 - current_hedge_ratio, tol_abs)
        unhedged_loss = current_worst_loss / unhedged_fraction
        return HedgeRecommendationV1(
            contract_version="v1",
            current_hedge_ratio=current_hedge_ratio,
            target_worst_loss_domestic=target,
            implied_worst_loss_unhedged_domestic=unhedged_loss,
            recommended_hedge_ratio=current_hedge_ratio,
            expected_worst_loss_domestic=current_worst_loss,
        )

    unhedged_fraction = max(1.0 - current_hedge_ratio, tol_abs)
    unhedged_loss = current_worst_loss / unhedged_fraction
    required_unhedged_fraction = target / unhedged_loss
    recommended_hedge_ratio = _clamp01(1.0 - required_unhedged_fraction)
    expected_worst_loss = unhedged_loss * max(0.0, 1.0 - recommended_hedge_ratio)

    return HedgeRecommendationV1(
        contract_version="v1",
        current_hedge_ratio=current_hedge_ratio,
        target_worst_loss_domestic=target,
        implied_worst_loss_unhedged_domestic=unhedged_loss,
        recommended_hedge_ratio=recommended_hedge_ratio,
        expected_worst_loss_domestic=expected_worst_loss,
    )


__all__ = ["HedgeRecommendationV1", "recommend_hedge_ratio_v1"]
