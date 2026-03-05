from __future__ import annotations

from decimal import Decimal
from decimal import InvalidOperation

from core.services.advisory_output_contract_v1 import AdvisoryDecisionV1
from core.services.rolling_hedge_ladder_v1 import RollingHedgeLadderResultV1
from core.services.scenario_risk_summary_v1 import ScenarioRiskSummaryV1


def _to_decimal(value: object) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"invalid decimal value: {value!r}") from exc
    if not parsed.is_finite():
        raise ValueError(f"non-finite decimal value: {value!r}")
    return parsed


def _fmt_num(value: float | Decimal) -> str:
    # Deterministic fixed representation (not locale aware).
    return f"{float(value):,.2f}"


def _fmt_ratio(value: float) -> str:
    return f"{value:.6f}"


def _extract_spot_shock_pct(raw_label: str) -> float | None:
    marker = "spot_shock="
    if marker not in raw_label:
        return None
    value = raw_label.split(marker, 1)[1].split(",", 1)[0].strip()
    if value.endswith("%"):
        value = value[:-1]
    try:
        return float(value)
    except ValueError:
        return None


def _shock_display(raw_label: str) -> str:
    marker = "spot_shock="
    if marker not in raw_label:
        return ""
    return raw_label.split(marker, 1)[1].split(",", 1)[0].strip()


def _action_from_risk_summary(pair: str, risk_summary: ScenarioRiskSummaryV1) -> str:
    foreign_ccy = pair.split("/", 1)[0] if "/" in pair else pair
    worst_label = ""
    for row in risk_summary.scenario_rows:
        if row.scenario_id == risk_summary.worst_scenario_id:
            worst_label = row.label
            break

    shock = _extract_spot_shock_pct(worst_label)
    if shock is None:
        return "N/A"
    if shock > 0:
        return f"BUY {foreign_ccy} FWD"
    if shock < 0:
        return f"SELL {foreign_ccy} FWD"
    return "NO TRADE (NATURAL HEDGE)"


def _infer_global_notionals_from_ladder(
    ladder: RollingHedgeLadderResultV1,
) -> tuple[float, float, float, float]:
    gross_total = Decimal("0")
    current_total = Decimal("0")
    recommended_total = Decimal("0")

    for bucket in ladder.buckets:
        rec_notional = Decimal(str(bucket.recommended_forward_notional or 0.0))
        rec_ratio = Decimal(str(bucket.hedge_recommendation.recommended_hedge_ratio))
        cur_ratio = Decimal(str(bucket.current_hedge_ratio_effective))

        if rec_notional <= 0 or rec_ratio <= 0:
            continue

        gross = rec_notional / rec_ratio
        gross_total += gross
        current_total += gross * cur_ratio
        recommended_total += rec_notional

    additional_total = max(Decimal("0"), recommended_total - current_total)
    return float(gross_total), float(current_total), float(recommended_total), float(additional_total)


def render_advisory_report_markdown_v1(
    *,
    company_id: str,
    as_of_date: str,
    pair: str,
    decision: AdvisoryDecisionV1,
    risk_summary: ScenarioRiskSummaryV1,
    ladder: RollingHedgeLadderResultV1 | None,
) -> str:
    if not isinstance(company_id, str) or not company_id.strip():
        raise ValueError("company_id must be non-empty")
    if not isinstance(as_of_date, str) or not as_of_date.strip():
        raise ValueError("as_of_date must be non-empty")
    if not isinstance(pair, str) or not pair.strip():
        raise ValueError("pair must be non-empty")
    if not isinstance(decision, AdvisoryDecisionV1):
        raise ValueError("decision must be AdvisoryDecisionV1")
    if not isinstance(risk_summary, ScenarioRiskSummaryV1):
        raise ValueError("risk_summary must be ScenarioRiskSummaryV1")

    foreign_ccy = pair.split("/", 1)[0] if "/" in pair else pair

    pre_policy_ratio = float(decision.hedge_recommendation.recommended_hedge_ratio)
    post_policy_ratio = pre_policy_ratio

    net_abs_foreign: float | None = None
    current_hedge_notional: float | None = None
    recommended_hedge_notional: float | None = None
    additional_notional: float | None = None
    target_total_domestic: float | None = None

    if ladder is not None:
        net_abs_foreign, current_hedge_notional, recommended_hedge_notional, additional_notional = (
            _infer_global_notionals_from_ladder(ladder)
        )
        if net_abs_foreign > 0:
            post_policy_ratio = recommended_hedge_notional / net_abs_foreign
        target_total_domestic = float(
            sum(_to_decimal(bucket.hedge_recommendation.target_worst_loss_domestic) for bucket in ladder.buckets)
        )

    action = _action_from_risk_summary(pair, risk_summary)
    if net_abs_foreign is None:
        net_foreign_display = f"N/A {foreign_ccy}"
        abs_foreign_display = f"N/A {foreign_ccy}"
        net_type = "N/A"
    else:
        signed = net_abs_foreign
        net_type = "NET RECEIVABLE"
        if action.startswith("BUY"):
            signed = -net_abs_foreign
            net_type = "NET PAYABLE"
        elif action.startswith("NO TRADE"):
            signed = 0.0
            net_type = "NET FLAT"
        net_foreign_display = f"{_fmt_num(signed)} {foreign_ccy}"
        abs_foreign_display = f"{_fmt_num(net_abs_foreign)} {foreign_ccy}"

    bindings: list[str] = []
    if ladder is not None:
        for bucket in ladder.buckets:
            if bucket.policy_result is not None:
                bindings.extend(bucket.policy_result.binding_constraints)
    if not bindings:
        bindings = list(decision.notes)
    bindings_display = ", ".join(sorted(set(bindings))) if bindings else "N/A"

    worst_label = "N/A"
    for row in risk_summary.scenario_rows:
        if row.scenario_id == risk_summary.worst_scenario_id:
            worst_label = _shock_display(row.label) or "N/A"
            break

    lines: list[str] = []
    lines.append("# Treasury Hedge Advisory — v1")

    lines.append("")
    lines.append("## Snapshot")
    lines.append(f"- Company: {company_id}")
    lines.append(f"- Pair: {pair}")
    lines.append(f"- As-of date: {as_of_date}")
    lines.append(f"- market_snapshot_id: {decision.snapshot_id}")

    lines.append("")
    lines.append("## Executive Takeaway")
    lines.append(
        f"- Coverage uplift: {_fmt_ratio(decision.hedge_recommendation.current_hedge_ratio)} "
        f"-> {_fmt_ratio(post_policy_ratio)} ({bindings_display})"
    )
    lines.append(
        f"- Tail scenario: {worst_label} | "
        f"Worst loss: {_fmt_num(abs(risk_summary.worst_loss_domestic))} (domestic)"
    )
    objective_value = _fmt_num(target_total_domestic) if target_total_domestic is not None else "N/A"
    lines.append(f"- Objective: cap tail loss to {objective_value} (domestic)")
    if recommended_hedge_notional is None:
        lines.append(
            f"- Action: {action} +N/A to reach N/A total"
        )
    else:
        lines.append(
            f"- Action: {action} +{_fmt_num(additional_notional or 0.0)} "
            f"to reach {_fmt_num(recommended_hedge_notional)} total"
        )

    lines.append("")
    lines.append("## Exposure Summary")
    lines.append(f"- net exposure foreign: {net_foreign_display}")
    lines.append(f"- net exposure type: {net_type}")
    lines.append(f"- abs foreign: {abs_foreign_display}")
    lines.append(f"- current ratio: {_fmt_ratio(decision.hedge_recommendation.current_hedge_ratio)}")
    if ladder is not None and abs(pre_policy_ratio - post_policy_ratio) > 1e-12:
        lines.append(f"- recommended ratio (pre policy): {_fmt_ratio(pre_policy_ratio)}")
    lines.append(f"- recommended ratio (post policy): {_fmt_ratio(post_policy_ratio)}")
    lines.append(f"- bindings: {bindings_display}")

    lines.append("")
    lines.append("## Risk Summary")
    lines.append(f"- worst scenario: shock={worst_label}, scenario_id={risk_summary.worst_scenario_id}")
    lines.append(f"- worst loss domestic: {_fmt_num(abs(risk_summary.worst_loss_domestic))}")
    if target_total_domestic is not None:
        lines.append(f"- target worst loss total (domestic): {_fmt_num(target_total_domestic)}")
    delta_text = "N/A" if decision.delta_exposure_aggregate_domestic is None else _fmt_num(decision.delta_exposure_aggregate_domestic)
    lines.append(f"- delta aggregate: {delta_text}")
    lines.append("- NOTE: per 1% spot move")

    lines.append("")
    lines.append("## Scenario P&L Table")
    lines.append("| Shock | Scenario ID | Total PV (domestic) | PnL vs Base (domestic) |")
    lines.append("|---|---|---:|---:|")
    for row in risk_summary.scenario_rows:
        lines.append(
            f"| {_shock_display(row.label)} | {row.scenario_id} | {_fmt_num(row.total_pv_domestic)} | {_fmt_num(row.pnl_vs_base_domestic)} |"
        )

    lines.append("")
    lines.append("## Hedge Trade Ticket")
    if additional_notional is None:
        lines.append(
            f"- Summary: {action} +N/A (raise hedge to {_fmt_ratio(post_policy_ratio)})"
        )
    else:
        lines.append(
            f"- Summary: {action} +{_fmt_num(additional_notional)} "
            f"(raise hedge to {_fmt_ratio(post_policy_ratio)})"
        )
    lines.append(f"- ACTION: {action}")
    if net_abs_foreign is None:
        lines.append(f"- Additional notional (foreign): N/A {foreign_ccy}")
        lines.append(f"- Current hedge notional: N/A {foreign_ccy}")
        lines.append(f"- Recommended hedge notional: N/A {foreign_ccy}")
    else:
        lines.append(f"- Additional notional (foreign): {_fmt_num(additional_notional or 0.0)} {foreign_ccy}")
        lines.append(f"- Current hedge notional: {_fmt_num(current_hedge_notional or 0.0)} {foreign_ccy}")
        lines.append(f"- Recommended hedge notional: {_fmt_num(recommended_hedge_notional or 0.0)} {foreign_ccy}")

    lines.append("")
    lines.append("## Rolling Hedge Ladder")
    if ladder is None:
        lines.append("N/A")
    else:
        lines.append("| Bucket | Target alloc (domestic) | Action | Additional notional (foreign) | Recommended ratio | Notes/bindings |")
        lines.append("|---|---:|---|---:|---:|---|")
        for bucket in ladder.buckets:
            bucket_action = _action_from_risk_summary(pair, bucket.risk_summary)
            bucket_notes = ""
            if bucket.policy_result is not None and bucket.policy_result.binding_constraints:
                bucket_notes = ", ".join(bucket.policy_result.binding_constraints)
            rec_notional = float(bucket.recommended_forward_notional or 0.0)
            rec_ratio = float(bucket.hedge_recommendation.recommended_hedge_ratio)
            cur_ratio = float(bucket.current_hedge_ratio_effective)
            if rec_ratio > 0.0:
                bucket_current = rec_notional * (cur_ratio / rec_ratio)
            else:
                bucket_current = 0.0
            bucket_additional = max(0.0, rec_notional - bucket_current)

            lines.append(
                f"| {bucket.bucket_label} | {_fmt_num(bucket.hedge_recommendation.target_worst_loss_domestic)} "
                f"| {bucket_action} | {_fmt_num(bucket_additional)} {foreign_ccy} "
                f"| {_fmt_ratio(bucket.hedge_recommendation.recommended_hedge_ratio)} | {bucket_notes} |"
            )

    lines.append("")
    lines.append("## Audit")
    lines.append("- Determinism: deterministic by construction (inputs + snapshot_id)")
    lines.append("- Units note: delta is per 1% spot shock")
    lines.append("- Non-goals: execution, optimization, VaR/ES")

    return "\n".join(lines)


__all__ = ["render_advisory_report_markdown_v1"]
