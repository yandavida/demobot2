from __future__ import annotations

from core.treasury.treasury_copilot_renderer_v1 import render_generic_answer_v1
from treasury_copilot_v1 import CopilotArtifactsV1
from treasury_copilot_v1 import CopilotAuditV1
from treasury_copilot_v1 import CopilotContextV1
from treasury_copilot_v1 import TreasuryCopilotRequestV1
from treasury_copilot_v1 import TreasuryCopilotResponseV1
from treasury_copilot_v1 import TreasuryIntentV1
from treasury_copilot_v1 import run_treasury_copilot_v1


def test_missing_context_renders_bullets_deterministically() -> None:
    resp = TreasuryCopilotResponseV1(
        intent=TreasuryIntentV1.RUN_FX_HEDGE_ADVISORY,
        answer_text=None,
        artifacts=None,
        warnings=[],
        missing_context=["market_snapshot_id", "policy_template_id"],
        audit=CopilotAuditV1(
            intent=TreasuryIntentV1.RUN_FX_HEDGE_ADVISORY,
            normalized_question="תעשה גידור",
        ),
    )

    out = render_generic_answer_v1(resp)

    assert "- market_snapshot_id" in out
    assert "- policy_template_id" in out
    assert out.index("market_snapshot_id") < out.index("policy_template_id")
    assert "ספקי את המזהים האלה והנסי שוב." in out


def test_intent_not_implemented_renders_stable_message() -> None:
    resp = TreasuryCopilotResponseV1(
        intent=TreasuryIntentV1.SHOW_SCENARIO_TABLE,
        answer_text=None,
        artifacts=None,
        warnings=["intent_not_implemented_v1"],
        missing_context=[],
        audit=CopilotAuditV1(
            intent=TreasuryIntentV1.SHOW_SCENARIO_TABLE,
            normalized_question="תראה לי טבלת תרחישים",
        ),
    )

    out = render_generic_answer_v1(resp)

    assert "SHOW_SCENARIO_TABLE" in out
    assert "המימוש עדיין לא הופעל" in out


def test_renderer_is_deterministic() -> None:
    resp = TreasuryCopilotResponseV1(
        intent=TreasuryIntentV1.SHOW_HEDGE_LADDER,
        answer_text=None,
        artifacts=None,
        warnings=["intent_not_implemented_v1"],
        missing_context=[],
        audit=CopilotAuditV1(
            intent=TreasuryIntentV1.SHOW_HEDGE_LADDER,
            normalized_question="show ladder",
        ),
    )

    assert render_generic_answer_v1(resp) == render_generic_answer_v1(resp)


def test_router_integration_missing_context_answer_text() -> None:
    req = TreasuryCopilotRequestV1(
        question="תעשה גידור",
        context=CopilotContextV1(
            market_snapshot_id=None,
            scenario_template_id=None,
            policy_template_id=None,
            portfolio_ref=None,
        ),
    )

    out = run_treasury_copilot_v1(req)

    assert out.answer_text is not None
    assert out.answer_text.startswith("חסר הקשר נדרש לביצוע הפעולה")
    assert "- market_snapshot_id" in out.answer_text


def test_explain_followup_renders_hebrew_sections_deterministically() -> None:
    artifacts = CopilotArtifactsV1(
        advisory_decision=None,
        explainability={
            "items": [
                {"code": "OBJECTIVE", "message": "Target worst-loss cap is 100000 domestic.", "data": {}},
                {"code": "TAIL_RISK", "message": "Worst-case scenario is spot_shock=+7.00%.", "data": {}},
                {"code": "COVERAGE_UPLIFT", "message": "Coverage moves from 0.350000 to 0.700000.", "data": {}},
                {"code": "POLICY_BINDINGS", "message": "Policy bindings triggered: MAX_HEDGE_RATIO.", "data": {}},
                {"code": "LADDER_DETAIL", "message": "Ladder has 4 buckets.", "data": {}},
            ],
            "summary_line": "0.35->0.70 | tail=100000",
        },
        report_markdown=None,
        scenario_table_markdown=None,
        ladder_table_markdown=None,
    )
    resp = TreasuryCopilotResponseV1(
        intent=TreasuryIntentV1.EXPLAIN_FX_DECISION,
        answer_text=None,
        artifacts=artifacts,
        warnings=["read_only_followup_v1"],
        missing_context=[],
        audit=CopilotAuditV1(
            intent=TreasuryIntentV1.EXPLAIN_FX_DECISION,
            normalized_question="למה המלצת",
        ),
    )

    out1 = render_generic_answer_v1(resp)
    out2 = render_generic_answer_v1(resp)

    assert "הסבר ההחלטה:" in out1
    assert "- יעד:" in out1
    assert "- סיכון זנב:" in out1
    assert "- שיפור כיסוי:" in out1
    assert "- מגבלות מחייבות:" in out1
    assert "- הערת סולם:" in out1
    assert out1 == out2


def test_scenario_followup_prefers_prerendered_markdown() -> None:
    table = "|A|B|\n|---|---|\n|1|2|"
    resp = TreasuryCopilotResponseV1(
        intent=TreasuryIntentV1.SHOW_SCENARIO_TABLE,
        answer_text=None,
        artifacts=CopilotArtifactsV1(
            advisory_decision=None,
            explainability=None,
            report_markdown=None,
            scenario_table_markdown=table,
            ladder_table_markdown=None,
        ),
        warnings=["read_only_followup_v1"],
        missing_context=[],
        audit=CopilotAuditV1(
            intent=TreasuryIntentV1.SHOW_SCENARIO_TABLE,
            normalized_question="טבלת תרחישים",
        ),
    )

    out = render_generic_answer_v1(resp)

    assert out.startswith("להלן טבלת התרחישים:")
    assert table in out


def test_ladder_followup_prefers_prerendered_markdown() -> None:
    table = "|Bucket|Action|\n|---|---|\n|0-30|BUY|"
    resp = TreasuryCopilotResponseV1(
        intent=TreasuryIntentV1.SHOW_HEDGE_LADDER,
        answer_text=None,
        artifacts=CopilotArtifactsV1(
            advisory_decision=None,
            explainability=None,
            report_markdown=None,
            scenario_table_markdown=None,
            ladder_table_markdown=table,
        ),
        warnings=["read_only_followup_v1"],
        missing_context=[],
        audit=CopilotAuditV1(
            intent=TreasuryIntentV1.SHOW_HEDGE_LADDER,
            normalized_question="סולם גידור",
        ),
    )

    out = render_generic_answer_v1(resp)

    assert out.startswith("להלן סולם הגידור:")
    assert table in out


def test_followup_fallbacks_when_artifacts_missing() -> None:
    explain_resp = TreasuryCopilotResponseV1(
        intent=TreasuryIntentV1.EXPLAIN_FX_DECISION,
        answer_text=None,
        artifacts=CopilotArtifactsV1(None, None, None, None, None),
        warnings=["read_only_followup_v1"],
        missing_context=[],
        audit=CopilotAuditV1(TreasuryIntentV1.EXPLAIN_FX_DECISION, "explain"),
    )
    scenario_resp = TreasuryCopilotResponseV1(
        intent=TreasuryIntentV1.SHOW_SCENARIO_TABLE,
        answer_text=None,
        artifacts=CopilotArtifactsV1(None, None, None, None, None),
        warnings=["read_only_followup_v1"],
        missing_context=[],
        audit=CopilotAuditV1(TreasuryIntentV1.SHOW_SCENARIO_TABLE, "scenario"),
    )
    ladder_resp = TreasuryCopilotResponseV1(
        intent=TreasuryIntentV1.SHOW_HEDGE_LADDER,
        answer_text=None,
        artifacts=CopilotArtifactsV1(None, None, None, None, None),
        warnings=["read_only_followup_v1"],
        missing_context=[],
        audit=CopilotAuditV1(TreasuryIntentV1.SHOW_HEDGE_LADDER, "ladder"),
    )

    assert render_generic_answer_v1(explain_resp) == "אין explainability להצגה עבור decision ref זה."
    assert render_generic_answer_v1(scenario_resp) == "אין טבלת תרחישים זמינה עבור decision ref זה."
    assert render_generic_answer_v1(ladder_resp) == "אין סולם גידור זמין עבור decision ref זה."
