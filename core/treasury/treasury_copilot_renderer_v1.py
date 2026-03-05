from __future__ import annotations


def _artifacts_value(artifacts: object, field_name: str):
    if artifacts is None:
        return None
    if isinstance(artifacts, dict):
        return artifacts.get(field_name)
    return getattr(artifacts, field_name, None)


def _as_non_empty_str(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    return text


def _find_explainability_item(items: list[object], code: str) -> dict | None:
    for item in items:
        if isinstance(item, dict) and str(item.get("code", "")) == code:
            return item
    return None


def _extract_explainability_items(explainability: object) -> list[object]:
    if explainability is None:
        return []
    if isinstance(explainability, dict):
        raw_items = explainability.get("items")
        return list(raw_items) if isinstance(raw_items, list) else []
    raw_items = getattr(explainability, "items", None)
    return list(raw_items) if isinstance(raw_items, tuple | list) else []


def _extract_explainability_summary_line(explainability: object) -> str | None:
    if explainability is None:
        return None
    if isinstance(explainability, dict):
        return _as_non_empty_str(explainability.get("summary_line"))
    return _as_non_empty_str(getattr(explainability, "summary_line", None))


def _extract_data_field(item: dict | None, key: str) -> str | None:
    if item is None:
        return None
    data = item.get("data")
    if not isinstance(data, dict):
        return None
    value = data.get(key)
    if isinstance(value, list):
        if not value:
            return None
        return ", ".join(str(v) for v in value)
    return _as_non_empty_str(value)


def _render_explain_followup_answer_v1(artifacts: object) -> str:
    explainability = _artifacts_value(artifacts, "explainability")
    if explainability is None:
        return "אין explainability להצגה עבור decision ref זה."

    items = _extract_explainability_items(explainability)
    objective = _find_explainability_item(items, "OBJECTIVE")
    tail_risk = _find_explainability_item(items, "TAIL_RISK")
    coverage_uplift = _find_explainability_item(items, "COVERAGE_UPLIFT")
    policy_bindings = _find_explainability_item(items, "POLICY_BINDINGS")
    limit_bindings = _find_explainability_item(items, "LIMIT_BINDINGS")
    ladder_detail = _find_explainability_item(items, "LADDER_DETAIL")

    lines: list[str] = ["הסבר ההחלטה:"]

    objective_msg = _as_non_empty_str(objective.get("message")) if objective is not None else None
    if objective_msg is not None:
        lines.append(f"- יעד: {objective_msg}")

    tail_msg = _as_non_empty_str(tail_risk.get("message")) if tail_risk is not None else None
    if tail_msg is not None:
        lines.append(f"- סיכון זנב: {tail_msg}")

    coverage_msg = _as_non_empty_str(coverage_uplift.get("message")) if coverage_uplift is not None else None
    if coverage_msg is not None:
        lines.append(f"- שיפור כיסוי: {coverage_msg}")

    bindings_parts: list[str] = []
    policy_msg = _as_non_empty_str(policy_bindings.get("message")) if policy_bindings is not None else None
    if policy_msg is not None:
        bindings_parts.append(policy_msg)
    limit_msg = _as_non_empty_str(limit_bindings.get("message")) if limit_bindings is not None else None
    if limit_msg is not None:
        bindings_parts.append(limit_msg)
    if bindings_parts:
        lines.append(f"- מגבלות מחייבות: {' | '.join(bindings_parts)}")

    ladder_msg = _as_non_empty_str(ladder_detail.get("message")) if ladder_detail is not None else None
    if ladder_msg is not None:
        lines.append(f"- הערת סולם: {ladder_msg}")

    summary_line = _extract_explainability_summary_line(explainability)
    if summary_line is not None:
        lines.append(f"- סיכום: {summary_line}")

    if len(lines) == 1:
        return "אין explainability להצגה עבור decision ref זה."
    return "\n".join(lines)


def _render_scenario_table_from_structured_artifacts_v1(artifacts: object) -> str | None:
    advisory_decision = _artifacts_value(artifacts, "advisory_decision")
    if not isinstance(advisory_decision, dict):
        return None
    risk_summary = advisory_decision.get("risk_summary")
    if not isinstance(risk_summary, dict):
        return None
    scenario_rows = risk_summary.get("scenario_rows")
    if not isinstance(scenario_rows, list) or not scenario_rows:
        return None

    headers = ["Shock", "Scenario ID", "Total PV (domestic)", "PnL vs Base (domestic)"]
    rows: list[list[str]] = []
    for row in scenario_rows:
        if not isinstance(row, dict):
            continue
        rows.append(
            [
                str(row.get("label", "")),
                str(row.get("scenario_id", "")),
                str(row.get("total_pv_domestic", "")),
                str(row.get("pnl_vs_base_domestic", "")),
            ]
        )
    if not rows:
        return None
    return render_markdown_table_v1(headers, rows)


def _render_ladder_table_from_structured_artifacts_v1(artifacts: object) -> str | None:
    explainability = _artifacts_value(artifacts, "explainability")
    items = _extract_explainability_items(explainability)
    ladder_detail = _find_explainability_item(items, "LADDER_DETAIL")
    top_actions = _extract_data_field(ladder_detail, "top_bucket_actions")
    if top_actions is None:
        return None
    headers = ["Field", "Value"]
    rows = [["top_bucket_actions", top_actions]]
    return render_markdown_table_v1(headers, rows)


def _render_scenario_followup_answer_v1(artifacts: object) -> str:
    pre_rendered = _as_non_empty_str(_artifacts_value(artifacts, "scenario_table_markdown"))
    if pre_rendered is not None:
        return "להלן טבלת התרחישים:\n" + pre_rendered

    rendered = _render_scenario_table_from_structured_artifacts_v1(artifacts)
    if rendered is not None:
        return "להלן טבלת התרחישים:\n" + rendered

    return "אין טבלת תרחישים זמינה עבור decision ref זה."


def _render_ladder_followup_answer_v1(artifacts: object) -> str:
    pre_rendered = _as_non_empty_str(_artifacts_value(artifacts, "ladder_table_markdown"))
    if pre_rendered is not None:
        return "להלן סולם הגידור:\n" + pre_rendered

    rendered = _render_ladder_table_from_structured_artifacts_v1(artifacts)
    if rendered is not None:
        return "להלן סולם הגידור:\n" + rendered

    return "אין סולם גידור זמין עבור decision ref זה."

def _intent_token(intent: object) -> str:
    value = getattr(intent, "value", None)
    return str(value) if value is not None else str(intent)


def render_missing_context_answer_v1(intent: object, missing_context: list[str]) -> str:
    lines: list[str] = []
    lines.append(f"חסר הקשר נדרש לביצוע הפעולה {_intent_token(intent)}.")
    for field_name in missing_context:
        lines.append(f"- {field_name}")
    lines.append("ספקי את המזהים האלה והנסי שוב.")
    return "\n".join(lines)


def render_not_implemented_answer_v1(intent: object) -> str:
    return (
        f"הבקשה זוהתה כ-{_intent_token(intent)} אבל המימוש עדיין לא הופעל. "
        "ניתוב ואימות הקשר פעילים, אבל החיבור למנועים עדיין לא חווט."
    )


def render_markdown_table_v1(headers: list[str], rows: list[list[str]]) -> str:
    header_line = "| " + " | ".join(headers) + " |"
    sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    row_lines = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_line, sep_line, *row_lines])


def render_scenario_table_markdown_v1(table: str | None) -> str | None:
    if table is None:
        return None
    return table


def render_ladder_table_markdown_v1(table: str | None) -> str | None:
    if table is None:
        return None
    return table


def render_generic_answer_v1(resp: object) -> str:
    missing_context = list(getattr(resp, "missing_context", []))
    warnings = list(getattr(resp, "warnings", []))
    artifacts = getattr(resp, "artifacts", None)
    intent = getattr(resp, "intent", "UNKNOWN")

    if missing_context:
        return render_missing_context_answer_v1(intent, missing_context)

    if "intent_not_implemented_v1" in warnings:
        return render_not_implemented_answer_v1(intent)

    if "followup_resolution_failed_v1" in warnings or "resolution_failed_v1" in warnings:
        return "לא ניתן לטעון תוצרים עבור הבקשה הזו כרגע."

    if artifacts is None:
        return "התקבל. אין תוצרים להצגה כרגע."

    intent_token = _intent_token(intent)
    if intent_token == "EXPLAIN_FX_DECISION":
        return _render_explain_followup_answer_v1(artifacts)
    if intent_token == "SHOW_SCENARIO_TABLE":
        return _render_scenario_followup_answer_v1(artifacts)
    if intent_token == "SHOW_HEDGE_LADDER":
        return _render_ladder_followup_answer_v1(artifacts)

    available: list[str] = []
    if getattr(artifacts, "advisory_decision", None) is not None:
        available.append("advisory_decision")
    if getattr(artifacts, "explainability", None) is not None:
        available.append("explainability")
    if getattr(artifacts, "report_markdown", None):
        available.append("report_markdown")
    if getattr(artifacts, "scenario_table_markdown", None):
        available.append("scenario_table_markdown")
    if getattr(artifacts, "ladder_table_markdown", None):
        available.append("ladder_table_markdown")

    if not available:
        return "התקבל. אין תוצרים להצגה כרגע."

    return "התקבלו תוצרים זמינים: " + ", ".join(available)


__all__ = [
    "render_missing_context_answer_v1",
    "render_not_implemented_answer_v1",
    "render_markdown_table_v1",
    "render_scenario_table_markdown_v1",
    "render_ladder_table_markdown_v1",
    "render_generic_answer_v1",
]
