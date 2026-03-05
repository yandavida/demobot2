from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.services.advisory_input_contract_v1 import normalize_advisory_input_v1
from core.services.advisory_read_model_v1 import run_treasury_advisory_v1
from core.services.advisory_report_v1 import render_advisory_report_markdown_v1
from core.services.explainability_pack_v1 import build_explainability_pack_v1
from core.treasury.copilot_artifact_bundle_store_v1 import CopilotArtifactBundleNotFoundError
from core.treasury.copilot_artifact_bundle_store_v1 import CopilotArtifactBundleValidationError
from core.treasury.copilot_artifact_bundle_store_v1 import get_copilot_artifact_bundle_v1
from core.treasury.copilot_artifact_bundle_store_v1 import put_copilot_artifact_bundle_v1
from core.treasury.copilot_resolution_v1 import CopilotResolvedInputsV1
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
    as_of_decision_ref: str | None = None


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
    as_of_decision_ref: str | None = None


class FollowupResolutionError(ValueError):
    pass


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
    "as_of_decision_ref",
)

_REQUIRED_FIELDS_BY_INTENT_V1: dict[TreasuryIntentV1, tuple[str, ...]] = {
    TreasuryIntentV1.RUN_FX_HEDGE_ADVISORY: (
        "market_snapshot_id",
        "scenario_template_id",
        "policy_template_id",
        "portfolio_ref",
    ),
    TreasuryIntentV1.EXPLAIN_FX_DECISION: ("as_of_decision_ref",),
    TreasuryIntentV1.SHOW_SCENARIO_TABLE: ("as_of_decision_ref",),
    TreasuryIntentV1.SHOW_HEDGE_LADDER: ("as_of_decision_ref",),
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


def _extract_primary_pair_v1(advisory_payload: dict) -> str:
    normalized = normalize_advisory_input_v1(advisory_payload)
    if not normalized.exposures:
        raise ValueError("missing_exposures_for_report")
    return str(normalized.exposures[0].currency_pair)


def invoke_fx_advisory_pipeline_v1(resolved: CopilotResolvedInputsV1) -> CopilotArtifactsV1:
    decision = run_treasury_advisory_v1(
        payload=resolved.advisory_payload,
        base_snapshot=resolved.base_snapshot,
        scenario_spec=resolved.scenario_spec,
        target_worst_loss_domestic=float(resolved.target_worst_loss_domestic),
    )
    explainability = build_explainability_pack_v1(
        decision=decision,
        risk_summary=decision.risk_summary,
        ladder=None,
    )
    report_markdown = render_advisory_report_markdown_v1(
        company_id=decision.company_id,
        as_of_date=resolved.base_snapshot.as_of_ts.date().isoformat(),
        pair=_extract_primary_pair_v1(resolved.advisory_payload),
        decision=decision,
        risk_summary=decision.risk_summary,
        ladder=None,
    )
    return CopilotArtifactsV1(
        advisory_decision=decision,
        explainability=explainability,
        report_markdown=report_markdown,
        scenario_table_markdown=None,
        ladder_table_markdown=None,
    )


def _parse_decision_ref_v1(as_of_decision_ref: str) -> str:
    if not isinstance(as_of_decision_ref, str) or not as_of_decision_ref.strip():
        raise FollowupResolutionError("invalid_decision_ref")

    prefix = "artifact_bundle:"
    if not as_of_decision_ref.startswith(prefix):
        raise FollowupResolutionError("unsupported_decision_ref_format")

    artifact_id = as_of_decision_ref[len(prefix):].strip()
    if not artifact_id:
        raise FollowupResolutionError("invalid_decision_ref")
    return artifact_id


def resolve_decision_ref_to_copilot_artifacts_v1(as_of_decision_ref: str) -> CopilotArtifactsV1:
    artifact_id = _parse_decision_ref_v1(as_of_decision_ref)
    try:
        payload = get_copilot_artifact_bundle_v1(artifact_id)
    except CopilotArtifactBundleNotFoundError as exc:
        raise FollowupResolutionError(f"unknown_decision_ref:{artifact_id}") from exc
    except CopilotArtifactBundleValidationError as exc:
        raise FollowupResolutionError(f"invalid_decision_ref_payload:{artifact_id}") from exc

    return CopilotArtifactsV1(
        advisory_decision=payload.get("advisory_decision"),
        explainability=payload.get("explainability"),
        report_markdown=payload.get("report_markdown"),
        scenario_table_markdown=payload.get("scenario_table_markdown"),
        ladder_table_markdown=payload.get("ladder_table_markdown"),
    )


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
            resolved = resolve_copilot_inputs_fx_v1(req.context)
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

        artifacts = invoke_fx_advisory_pipeline_v1(resolved)
        bundle_id = put_copilot_artifact_bundle_v1(
            advisory_decision=artifacts.advisory_decision,
            explainability=artifacts.explainability,
            report_markdown=artifacts.report_markdown,
            scenario_table_markdown=artifacts.scenario_table_markdown,
            ladder_table_markdown=artifacts.ladder_table_markdown,
        )
        decision_ref = f"artifact_bundle:{bundle_id}"
        response = TreasuryCopilotResponseV1(
            intent=intent,
            answer_text=None,
            artifacts=artifacts,
            warnings=["fx_advisory_executed_v1"],
            missing_context=[],
            audit=CopilotAuditV1(
                intent=intent,
                normalized_question=normalized,
                as_of_decision_ref=decision_ref,
            ),
        )
        return TreasuryCopilotResponseV1(
            intent=response.intent,
            answer_text=render_generic_answer_v1(response),
            artifacts=response.artifacts,
            warnings=response.warnings,
            missing_context=response.missing_context,
            audit=response.audit,
        )

    if intent in (
        TreasuryIntentV1.EXPLAIN_FX_DECISION,
        TreasuryIntentV1.SHOW_SCENARIO_TABLE,
        TreasuryIntentV1.SHOW_HEDGE_LADDER,
    ):
        decision_ref = str(req.context.as_of_decision_ref or "")
        try:
            artifacts = resolve_decision_ref_to_copilot_artifacts_v1(decision_ref)
        except FollowupResolutionError as exc:
            response = TreasuryCopilotResponseV1(
                intent=intent,
                answer_text=None,
                artifacts=None,
                warnings=["followup_resolution_failed_v1", f"resolution_error:{str(exc)}"],
                missing_context=[],
                audit=CopilotAuditV1(
                    intent=intent,
                    normalized_question=normalized,
                    as_of_decision_ref=decision_ref,
                ),
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
            artifacts=artifacts,
            warnings=["read_only_followup_v1"],
            missing_context=[],
            audit=CopilotAuditV1(
                intent=intent,
                normalized_question=normalized,
                as_of_decision_ref=decision_ref,
            ),
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
    "invoke_fx_advisory_pipeline_v1",
    "resolve_decision_ref_to_copilot_artifacts_v1",
    "run_treasury_copilot_v1",
]
