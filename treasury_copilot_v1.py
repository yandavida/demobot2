from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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


__all__ = [
    "TreasuryIntentV1",
    "CopilotContextV1",
    "TreasuryCopilotRequestV1",
    "CopilotArtifactsV1",
    "CopilotAuditV1",
    "TreasuryCopilotResponseV1",
    "normalize_question_v1",
    "parse_intent_v1",
]
