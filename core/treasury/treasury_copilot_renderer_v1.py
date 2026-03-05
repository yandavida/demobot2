from __future__ import annotations

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

    if artifacts is None:
        return "התקבל. אין תוצרים להצגה כרגע."

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
