from __future__ import annotations

from dataclasses import dataclass

from core.services.advisory_output_contract_v1 import AdvisoryDecisionV1
from core.services.rolling_hedge_ladder_v1 import RollingHedgeLadderResultV1
from core.services.scenario_risk_summary_v1 import ScenarioRiskSummaryV1


@dataclass(frozen=True)
class ExplainabilityItemV1:
    code: str
    severity: str
    title: str
    message: str
    data: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "data": {str(k): self.data[k] for k in self.data},
        }


@dataclass(frozen=True)
class ExplainabilityPackV1:
    items: tuple[ExplainabilityItemV1, ...]
    summary_line: str

    def to_dict(self) -> dict[str, object]:
        return {
            "items": [item.to_dict() for item in self.items],
            "summary_line": self.summary_line,
        }


def _fmt_ratio(value: float) -> str:
    return f"{float(value):.6f}"


def _fmt_money(value: float) -> str:
    return f"{float(value):.2f}"


def _extract_worst_label(risk_summary: ScenarioRiskSummaryV1) -> str:
    for row in risk_summary.scenario_rows:
        if row.scenario_id == risk_summary.worst_scenario_id:
            return row.label
    return "N/A"


def _infer_post_policy_ratio_from_ladder(ladder: RollingHedgeLadderResultV1) -> float | None:
    gross_total = 0.0
    recommended_total = 0.0
    for bucket in ladder.buckets:
        rec_notional = float(bucket.recommended_forward_notional or 0.0)
        rec_ratio = float(bucket.hedge_recommendation.recommended_hedge_ratio)
        if rec_notional <= 0.0 or rec_ratio <= 0.0:
            continue
        gross_total += rec_notional / rec_ratio
        recommended_total += rec_notional
    if gross_total <= 0.0:
        return None
    return recommended_total / gross_total


def _target_total_from_ladder(ladder: RollingHedgeLadderResultV1) -> float:
    return float(sum(float(bucket.hedge_recommendation.target_worst_loss_domestic) for bucket in ladder.buckets))


def _ladder_top_actions(ladder: RollingHedgeLadderResultV1) -> list[str]:
    top: list[str] = []
    for bucket in ladder.buckets[:2]:
        current = float(bucket.current_hedge_ratio_effective)
        recommended = float(bucket.hedge_recommendation.recommended_hedge_ratio)
        action = "HOLD"
        if recommended > current:
            action = "INCREASE_HEDGE"
        elif recommended < current:
            action = "DECREASE_HEDGE"
        top.append(f"{bucket.bucket_label}:{action}")
    return top


def _get_limit_bindings(limit_result: object | None) -> tuple[list[str], str | None]:
    if limit_result is None:
        return [], None
    bindings_raw = getattr(limit_result, "binding_constraints", ())
    unmet_target_reason = getattr(limit_result, "unmet_target_reason", None)
    bindings = [str(item) for item in tuple(bindings_raw)]
    reason = None if unmet_target_reason is None else str(unmet_target_reason)
    return bindings, reason


def build_explainability_pack_v1(
    *,
    decision: AdvisoryDecisionV1,
    risk_summary: ScenarioRiskSummaryV1,
    ladder: RollingHedgeLadderResultV1 | None,
    limit_result: object | None = None,
) -> ExplainabilityPackV1:
    if not isinstance(decision, AdvisoryDecisionV1):
        raise ValueError("decision must be AdvisoryDecisionV1")
    if not isinstance(risk_summary, ScenarioRiskSummaryV1):
        raise ValueError("risk_summary must be ScenarioRiskSummaryV1")
    if ladder is not None and not isinstance(ladder, RollingHedgeLadderResultV1):
        raise ValueError("ladder must be RollingHedgeLadderResultV1 or None")

    current_ratio = float(decision.hedge_recommendation.current_hedge_ratio)
    post_policy_ratio = float(decision.hedge_recommendation.recommended_hedge_ratio)
    target_total_display = "N/A"
    target_total_value: float | None = None

    if ladder is not None:
        inferred = _infer_post_policy_ratio_from_ladder(ladder)
        if inferred is not None:
            post_policy_ratio = inferred
        target_total_value = _target_total_from_ladder(ladder)
        target_total_display = _fmt_money(target_total_value)

    items: list[ExplainabilityItemV1] = []

    worst_label = _extract_worst_label(risk_summary)
    worst_loss = abs(float(risk_summary.worst_loss_domestic))
    items.append(
        ExplainabilityItemV1(
            code="TAIL_RISK",
            severity="INFO",
            title="Tail Risk Driver",
            message=f"Worst-case scenario is {worst_label}; tail loss is {_fmt_money(worst_loss)} domestic.",
            data={
                "worst_shock_label": worst_label,
                "worst_loss_domestic": _fmt_money(worst_loss),
            },
        )
    )

    items.append(
        ExplainabilityItemV1(
            code="OBJECTIVE",
            severity="INFO",
            title="Risk Objective",
            message=(
                f"Target worst-loss cap is {target_total_display} domestic."
                if ladder is not None
                else "Target worst-loss cap is N/A (no ladder provided)."
            ),
            data={
                "target_worst_loss_total_domestic": target_total_display,
            },
        )
    )

    items.append(
        ExplainabilityItemV1(
            code="COVERAGE_UPLIFT",
            severity="INFO",
            title="Coverage Uplift",
            message=f"Coverage moves from {_fmt_ratio(current_ratio)} to {_fmt_ratio(post_policy_ratio)}.",
            data={
                "current_ratio": _fmt_ratio(current_ratio),
                "post_policy_ratio": _fmt_ratio(post_policy_ratio),
            },
        )
    )

    policy_bindings = [str(note) for note in decision.notes]
    if policy_bindings:
        items.append(
            ExplainabilityItemV1(
                code="POLICY_BINDINGS",
                severity="WARN",
                title="Policy Constraints Bound",
                message=f"Policy bindings triggered: {', '.join(policy_bindings)}.",
                data={
                    "binding_constraints": list(policy_bindings),
                },
            )
        )

    limit_bindings, limit_reason = _get_limit_bindings(limit_result)
    if limit_bindings or limit_reason is not None:
        message = "Limit bindings triggered"
        if limit_bindings:
            message = f"Limit bindings triggered: {', '.join(limit_bindings)}"
        if limit_reason is not None:
            message = f"{message}; reason={limit_reason}"
        items.append(
            ExplainabilityItemV1(
                code="LIMIT_BINDINGS",
                severity="WARN",
                title="Counterparty Limits Bound",
                message=f"{message}.",
                data={
                    "binding_constraints": list(limit_bindings),
                    "unmet_target_reason": limit_reason,
                },
            )
        )

    delta_value = decision.delta_exposure_aggregate_domestic
    delta_display = "N/A" if delta_value is None else _fmt_money(float(delta_value))
    items.append(
        ExplainabilityItemV1(
            code="DELTA_UNITS",
            severity="INFO",
            title="Delta Units",
            message=f"Delta is per 1% spot move; aggregate delta={delta_display}.",
            data={
                "delta_exposure_aggregate_domestic": delta_display,
                "units": "per_1pct_spot_move",
            },
        )
    )

    if ladder is not None:
        non_empty = sum(1 for bucket in ladder.buckets if bucket.exposures_count > 0)
        top_actions = _ladder_top_actions(ladder)
        items.append(
            ExplainabilityItemV1(
                code="LADDER_DETAIL",
                severity="INFO",
                title="Ladder Detail",
                message=f"Ladder has {len(ladder.buckets)} buckets ({non_empty} non-empty).",
                data={
                    "bucket_count": len(ladder.buckets),
                    "non_empty_bucket_count": non_empty,
                    "top_bucket_actions": top_actions,
                },
            )
        )

    summary_bindings: list[str] = []
    for token in policy_bindings:
        if token not in summary_bindings:
            summary_bindings.append(token)
    for token in limit_bindings:
        if token not in summary_bindings:
            summary_bindings.append(token)
    if limit_reason is not None and limit_reason not in summary_bindings:
        summary_bindings.append(limit_reason)

    bindings_text = ",".join(summary_bindings) if summary_bindings else "NONE"
    tail_text = _fmt_money(worst_loss)
    summary_line = (
        f"{_fmt_ratio(current_ratio)}→{_fmt_ratio(post_policy_ratio)}"
        f" | tail={tail_text}"
        f" | target={target_total_display}"
        f" | bindings={bindings_text}"
    )

    return ExplainabilityPackV1(items=tuple(items), summary_line=summary_line)


__all__ = [
    "ExplainabilityItemV1",
    "ExplainabilityPackV1",
    "build_explainability_pack_v1",
]
