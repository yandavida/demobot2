from __future__ import annotations

from core.treasury.treasury_copilot_renderer_v1 import render_generic_answer_v1
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
