from __future__ import annotations

from treasury_copilot_v1 import CopilotContextV1
from treasury_copilot_v1 import TreasuryCopilotRequestV1
from treasury_copilot_v1 import TreasuryIntentV1
from treasury_copilot_v1 import run_treasury_copilot_v1


def test_missing_context_returns_missing_context_and_audit() -> None:
    req = TreasuryCopilotRequestV1(
        question="תעשה גידור",
        context=CopilotContextV1(
            market_snapshot_id=None,
            scenario_template_id="scn-std-7",
            policy_template_id=None,
            portfolio_ref=None,
        ),
    )

    out = run_treasury_copilot_v1(req)

    assert out.intent == TreasuryIntentV1.RUN_FX_HEDGE_ADVISORY
    assert out.missing_context == ["market_snapshot_id", "policy_template_id", "portfolio_ref"]
    assert out.warnings == []
    assert out.artifacts is None
    assert out.answer_text is not None
    assert out.audit.normalized_question == "תעשה גידור"


def test_sufficient_context_returns_resolution_failure_warning() -> None:
    req = TreasuryCopilotRequestV1(
        question="תעשה גידור",
        context=CopilotContextV1(
            market_snapshot_id="snap-001",
            scenario_template_id="scn-std-7",
            policy_template_id="TREASURY_STANDARD_70",
            portfolio_ref="portfolio-a",
        ),
    )

    out = run_treasury_copilot_v1(req)

    assert out.intent == TreasuryIntentV1.RUN_FX_HEDGE_ADVISORY
    assert out.missing_context == []
    assert out.warnings[0] == "resolution_failed_v1"
    assert out.warnings[1].startswith("resolution_error:")
    assert out.artifacts is None
    assert out.answer_text is not None


def test_non_fx_intent_with_context_returns_not_implemented_warning() -> None:
    req = TreasuryCopilotRequestV1(
        question="תראה לי טבלת תרחישים",
        context=CopilotContextV1(
            market_snapshot_id=None,
            scenario_template_id="scn-std-7",
            policy_template_id=None,
            portfolio_ref=None,
        ),
    )

    out = run_treasury_copilot_v1(req)

    assert out.intent == TreasuryIntentV1.SHOW_SCENARIO_TABLE
    assert out.missing_context == []
    assert "intent_not_implemented_v1" in out.warnings
    assert out.artifacts is None
    assert out.answer_text is not None


def test_router_is_deterministic_for_same_request() -> None:
    req = TreasuryCopilotRequestV1(
        question="   תעשה   גידור   ",
        context=CopilotContextV1(
            market_snapshot_id=None,
            scenario_template_id=None,
            policy_template_id=None,
            portfolio_ref=None,
        ),
    )

    out1 = run_treasury_copilot_v1(req)
    out2 = run_treasury_copilot_v1(req)

    assert out1 == out2
    assert out1.missing_context == [
        "market_snapshot_id",
        "scenario_template_id",
        "policy_template_id",
        "portfolio_ref",
    ]
