from __future__ import annotations

from decimal import Decimal
from decimal import InvalidOperation
from typing import Iterable

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


def _fmt_money(value: float | Decimal) -> str:
    # Locale-independent fixed formatting for report stability.
    return f"{float(value):,.2f}"


def _fmt_ratio(value: float) -> str:
    return f"{value:.6f}"


def _extract_shock_label(raw_label: str) -> str:
    marker = "spot_shock="
    if marker not in raw_label:
        return ""
    rest = raw_label.split(marker, 1)[1]
    return rest.split(",", 1)[0].strip()


def _infer_exposure_action(*, delta_aggregate: float | None, pair: str) -> tuple[str, str]:
    foreign_ccy = pair.split("/", 1)[0] if "/" in pair else pair
    if delta_aggregate is None:
        return "N/A", foreign_ccy
    if delta_aggregate > 0:
        return f"SELL {foreign_ccy} FWD", foreign_ccy
    if delta_aggregate < 0:
        return f"BUY {foreign_ccy} FWD", foreign_ccy
    return "NO TRADE (NATURAL HEDGE)", foreign_ccy


def _bucket_notional_decomposition(recommended_notional: float | None, recommended_ratio: float, current_ratio: float) -> tuple[float | None, float | None, float | None]:
    if recommended_notional is None:
        return None, None, None
    if recommended_ratio <= 0.0:
        # If recommended ratio is zero, both current and additional notionals collapse to zero for report purposes.
        return 0.0, 0.0, 0.0

    gross = recommended_notional / recommended_ratio
    current = max(0.0, gross * current_ratio)
    additional = max(0.0, recommended_notional - current)
    return gross, current, additional


def _aggregate_bindings(rows: Iterable[str]) -> str:
    deduped = sorted({item for item in rows if item})
    return ", ".join(deduped) if deduped else "N/A"


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

    action, foreign_ccy = _infer_exposure_action(
        delta_aggregate=decision.delta_exposure_aggregate_domestic,
        pair=pair,
    )

    current_ratio = decision.hedge_recommendation.current_hedge_ratio
    recommended_ratio = decision.hedge_recommendation.recommended_hedge_ratio

    # Prefer ladder-derived notionals when available because AdvisoryDecisionV1 does not carry gross exposure notional.
    current_hedge_notional: float | None = None
    recommended_hedge_notional: float | None = None
    additional_notional: float | None = None
    inferred_net_abs_foreign: float | None = None

    ladder_binding_items: list[str] = []
    if ladder is not None:
        recommended_hedge_notional = float(ladder.totals.total_recommended_forward_notional or 0.0)

        gross_total = 0.0
        current_total = 0.0
        additional_total = 0.0
        for bucket in ladder.buckets:
            gross, current, additional = _bucket_notional_decomposition(
                recommended_notional=bucket.recommended_forward_notional,
                recommended_ratio=bucket.hedge_recommendation.recommended_hedge_ratio,
                current_ratio=bucket.current_hedge_ratio_effective,
            )
            if gross is not None:
                gross_total += gross
            if current is not None:
                current_total += current
            if additional is not None:
                additional_total += additional
            if bucket.policy_result is not None:
                ladder_binding_items.extend(bucket.policy_result.binding_constraints)

        if gross_total > 0.0:
            inferred_net_abs_foreign = gross_total
        current_hedge_notional = current_total
        additional_notional = additional_total

    bindings = _aggregate_bindings(ladder_binding_items)
    if bindings == "N/A" and decision.notes:
        bindings = _aggregate_bindings(decision.notes)

    net_type = "N/A"
    if action.startswith("BUY"):
        net_type = "NET PAYABLE"
    elif action.startswith("SELL"):
        net_type = "NET RECEIVABLE"
    elif action.startswith("NO TRADE"):
        net_type = "NET FLAT"

    lines: list[str] = []
    lines.append("# Treasury Hedge Advisory — v1")

    lines.append("")
    lines.append("## Snapshot")
    lines.append(f"- Company: {company_id}")
    lines.append(f"- Pair: {pair}")
    lines.append(f"- As-of date: {as_of_date}")
    lines.append(f"- market_snapshot_id: {decision.snapshot_id}")

    lines.append("")
    lines.append("## Exposure Summary")
    if inferred_net_abs_foreign is None:
        lines.append(f"- net exposure foreign: N/A {foreign_ccy}")
        lines.append(f"- net exposure type: {net_type}")
        lines.append(f"- abs foreign: N/A {foreign_ccy}")
    else:
        signed = inferred_net_abs_foreign if action.startswith("SELL") else -inferred_net_abs_foreign
        lines.append(f"- net exposure foreign: {_fmt_money(signed)} {foreign_ccy}")
        lines.append(f"- net exposure type: {net_type}")
        lines.append(f"- abs foreign: {_fmt_money(inferred_net_abs_foreign)} {foreign_ccy}")

    lines.append(f"- current ratio: {_fmt_ratio(current_ratio)}")
    lines.append(f"- recommended ratio (post policy): {_fmt_ratio(recommended_ratio)}")
    lines.append(f"- bindings: {bindings}")

    lines.append("")
    lines.append("## Risk Summary")
    worst_label = ""
    for row in risk_summary.scenario_rows:
        if row.scenario_id == risk_summary.worst_scenario_id:
            worst_label = _extract_shock_label(row.label)
            break
    lines.append(
        f"- worst scenario: shock={worst_label or 'N/A'}, "
        f"scenario_id={risk_summary.worst_scenario_id}"
    )
    lines.append(f"- worst loss domestic: {_fmt_money(abs(risk_summary.worst_loss_domestic))}")
    delta_display = "N/A" if decision.delta_exposure_aggregate_domestic is None else _fmt_money(decision.delta_exposure_aggregate_domestic)
    lines.append(f"- delta aggregate: {delta_display}")
    lines.append("- NOTE: per 1% spot move")

    lines.append("")
    lines.append("## Scenario P&L Table")
    lines.append("| Shock | Scenario ID | Total PV (domestic) | PnL vs Base (domestic) |")
    lines.append("|---|---|---:|---:|")
    for row in risk_summary.scenario_rows:
        lines.append(
            f"| {_extract_shock_label(row.label)} | {row.scenario_id} "
            f"| {_fmt_money(row.total_pv_domestic)} | {_fmt_money(row.pnl_vs_base_domestic)} |"
        )

    lines.append("")
    lines.append("## Hedge Trade Ticket")
    lines.append(f"- ACTION: {action}")
    if additional_notional is None:
        lines.append(f"- Additional notional (foreign): N/A {foreign_ccy}")
        lines.append(f"- Current hedge notional: N/A {foreign_ccy}")
        lines.append(f"- Recommended hedge notional: N/A {foreign_ccy}")
    else:
        lines.append(f"- Additional notional (foreign): {_fmt_money(additional_notional)} {foreign_ccy}")
        lines.append(f"- Current hedge notional: {_fmt_money(current_hedge_notional or 0.0)} {foreign_ccy}")
        lines.append(f"- Recommended hedge notional: {_fmt_money(recommended_hedge_notional or 0.0)} {foreign_ccy}")

    lines.append("")
    lines.append("## Rolling Hedge Ladder")
    if ladder is None:
        lines.append("N/A")
    else:
        lines.append("| Bucket | Target alloc (domestic) | Action | Additional notional (foreign) | Recommended ratio | Notes/bindings |")
        lines.append("|---|---:|---|---:|---:|---|")
        for bucket in ladder.buckets:
            bucket_action, _ = _infer_exposure_action(
                delta_aggregate=bucket.risk_summary.worst_loss_domestic,
                pair=pair,
            )
            _, bucket_current, bucket_additional = _bucket_notional_decomposition(
                recommended_notional=bucket.recommended_forward_notional,
                recommended_ratio=bucket.hedge_recommendation.recommended_hedge_ratio,
                current_ratio=bucket.current_hedge_ratio_effective,
            )
            note = ""
            if bucket.policy_result is not None and bucket.policy_result.binding_constraints:
                note = ", ".join(bucket.policy_result.binding_constraints)
            lines.append(
                f"| {bucket.bucket_label} | {_fmt_money(bucket.hedge_recommendation.target_worst_loss_domestic)} "
                f"| {bucket_action} | {_fmt_money(bucket_additional or 0.0)} {foreign_ccy} "
                f"| {_fmt_ratio(bucket.hedge_recommendation.recommended_hedge_ratio)} | {note} |"
            )

    lines.append("")
    lines.append("## Audit")
    lines.append("- Determinism: deterministic by construction (inputs + snapshot_id)")
    lines.append("- Units note: delta is per 1% spot shock")
    lines.append("- Non-goals: execution, optimization, VaR/ES")

    return "\n".join(lines)


__all__ = ["render_advisory_report_markdown_v1"]
