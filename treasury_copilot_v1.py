from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.treasury.copilot_resolution_v1 import CopilotResolutionError
from core.treasury.copilot_resolution_v1 import resolve_copilot_inputs_fx_v1
from core.treasury.treasury_copilot_renderer_v1 import render_generic_answer_v1


class TreasuryIntentV1(str, Enum):
    RUN_FX_HEDGE_ADVISORY = "RUN_FX_HEDGE_ADVISORY"
    EXPLAIN_FX_DECISION = "EXPLAIN_FX_DECISION"
    SHOW_SCENARIO_TABLE = "SHOW_SCENARIO_TABLE"
    SHOW_HEDGE_LADDER = "SHOW_HEDGE_LADDER"
    COMPARE_POLICIES = "COMPARE_POLICIES"


@dataclass(frozen=True)
class CopilotContextV1:
    market_snapshot_id: str | None
    scenario_template_id: str | None
    policy_template_id: str | None
    portfolio_ref: str | None


@dataclass(frozen=True)
class TreasuryCopilotRequestV1:
    question: str
    context: CopilotContextV1
    response_style: str = "standard"


@dataclass(frozen=True)
class CopilotArtifactsV1:
    advisory_decision: object | None
    explainability: object | None
    report_markdown: str | None
    scenario_table_markdown: str | None
    ladder_table_markdown: str | None


@dataclass(frozen=True)
class CopilotAuditV1:
    intent: TreasuryIntentV1
    normalized_question: str


@dataclass(frozen=True)
class TreasuryCopilotResponseV1:
    intent: TreasuryIntentV1
    answer_text: str | None
    artifacts: CopilotArtifactsV1 | None
    warnings: list[str]
    missing_context: list[str]
    audit: CopilotAuditV1


_FIELD_ORDER_V1: tuple[str, ...] = (
    "market_snapshot_id",
    "scenario_template_id",
    "policy_template_id",
    "portfolio_ref",
)

_REQUIRED_FIELDS_BY_INTENT_V1: dict[TreasuryIntentV1, tuple[str, ...]] = {
    TreasuryIntentV1.RUN_FX_HEDGE_ADVISORY: (
        "market_snapshot_id",
        "scenario_template_id",
        "policy_template_id",
        "portfolio_ref",
    ),
    TreasuryIntentV1.EXPLAIN_FX_DECISION: ("portfolio_ref",),
    TreasuryIntentV1.SHOW_SCENARIO_TABLE: ("scenario_template_id",),
    TreasuryIntentV1.SHOW_HEDGE_LADDER: ("portfolio_ref",),
    TreasuryIntentV1.COMPARE_POLICIES: ("policy_template_id", "portfolio_ref"),
}


def normalize_question_v1(question: str) -> str:
    if question is None:
        return ""
    return " ".join(str(question).lower().strip().split())


def parse_intent_v1(question: str) -> TreasuryIntentV1:
    normalized = normalize_question_v1(question)

    if any(token in normalized for token in ("למה", "מדוע", "הסבר", "explain", "why")):
        return TreasuryIntentV1.EXPLAIN_FX_DECISION

    if any(token in normalized for token in ("תרחיש", "תרחישים", "scenario")):
        return TreasuryIntentV1.SHOW_SCENARIO_TABLE

    if any(token in normalized for token in ("ladder", "סולם", "בקט", "bucket")):
        return TreasuryIntentV1.SHOW_HEDGE_LADDER

    if any(token in normalized for token in ("השווה", "compare", "מדיניות", "policy")):
        return TreasuryIntentV1.COMPARE_POLICIES

    if any(token in normalized for token in ("גידור", "hedge", "forward", "ratio")):
        return TreasuryIntentV1.RUN_FX_HEDGE_ADVISORY

    return TreasuryIntentV1.RUN_FX_HEDGE_ADVISORY


def _is_missing_context_value(value: str | None) -> bool:
    if value is None:
        return True
    return not str(value).strip()


def validate_context_for_intent_v1(intent: TreasuryIntentV1, context: CopilotContextV1) -> list[str]:
    required = _REQUIRED_FIELDS_BY_INTENT_V1.get(intent, ())
    missing: list[str] = []
    for field_name in _FIELD_ORDER_V1:
        if field_name not in required:
            continue
        if _is_missing_context_value(getattr(context, field_name)):
            missing.append(field_name)
    return missing


def run_treasury_copilot_v1(req: TreasuryCopilotRequestV1) -> TreasuryCopilotResponseV1:
    normalized = normalize_question_v1(req.question)
    intent = parse_intent_v1(normalized)
    missing = validate_context_for_intent_v1(intent, req.context)

    if missing:
        response = TreasuryCopilotResponseV1(
            intent=intent,
            answer_text=None,
            artifacts=None,
            warnings=[],
            missing_context=missing,
            audit=CopilotAuditV1(intent=intent, normalized_question=normalized),
        )
        return TreasuryCopilotResponseV1(
            intent=response.intent,
            answer_text=render_generic_answer_v1(response),
            artifacts=response.artifacts,
            warnings=response.warnings,
            missing_context=response.missing_context,
            audit=response.audit,
        )

    if intent == TreasuryIntentV1.RUN_FX_HEDGE_ADVISORY:
        try:
            resolve_copilot_inputs_fx_v1(req.context)
        except CopilotResolutionError as exc:
            response = TreasuryCopilotResponseV1(
                intent=intent,
                answer_text=None,
                artifacts=None,
                warnings=["resolution_failed_v1", f"resolution_error:{str(exc)}"],
                missing_context=[],
                audit=CopilotAuditV1(intent=intent, normalized_question=normalized),
            )
            return TreasuryCopilotResponseV1(
                intent=response.intent,
                answer_text=render_generic_answer_v1(response),
                artifacts=response.artifacts,
                warnings=response.warnings,
                missing_context=response.missing_context,
                audit=response.audit,
            )

        response = TreasuryCopilotResponseV1(
            intent=intent,
            answer_text=None,
            artifacts=None,
            warnings=["resolution_ready_v1", "intent_not_implemented_v1"],
            missing_context=[],
            audit=CopilotAuditV1(intent=intent, normalized_question=normalized),
        )
        return TreasuryCopilotResponseV1(
            intent=response.intent,
            answer_text=render_generic_answer_v1(response),
            artifacts=response.artifacts,
            warnings=response.warnings,
            missing_context=response.missing_context,
            audit=response.audit,
        )

    response = TreasuryCopilotResponseV1(
        intent=intent,
        answer_text=None,
        artifacts=None,
        warnings=["intent_not_implemented_v1"],
        missing_context=[],
        audit=CopilotAuditV1(intent=intent, normalized_question=normalized),
    )
    return TreasuryCopilotResponseV1(
        intent=response.intent,
        answer_text=render_generic_answer_v1(response),
        artifacts=response.artifacts,
        warnings=response.warnings,
        missing_context=response.missing_context,
        audit=response.audit,
    )


__all__ = [
    "TreasuryIntentV1",
    "CopilotContextV1",
    "TreasuryCopilotRequestV1",
    "CopilotArtifactsV1",
    "CopilotAuditV1",
    "TreasuryCopilotResponseV1",
    "normalize_question_v1",
    "parse_intent_v1",
    "validate_context_for_intent_v1",
    "run_treasury_copilot_v1",
]
