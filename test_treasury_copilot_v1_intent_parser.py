from __future__ import annotations

from treasury_copilot_v1 import TreasuryIntentV1
from treasury_copilot_v1 import parse_intent_v1


def test_basic_intent_detection() -> None:
    assert parse_intent_v1("תעשה גידור לחשיפה הזאת") == TreasuryIntentV1.RUN_FX_HEDGE_ADVISORY
    assert parse_intent_v1("למה המלצת על 70%") == TreasuryIntentV1.EXPLAIN_FX_DECISION
    assert parse_intent_v1("תראה לי טבלת תרחישים") == TreasuryIntentV1.SHOW_SCENARIO_TABLE
    assert parse_intent_v1("תראה ladder לפי בקטים") == TreasuryIntentV1.SHOW_HEDGE_LADDER
    assert parse_intent_v1("השווה בין policies") == TreasuryIntentV1.COMPARE_POLICIES


def test_precedence_rules() -> None:
    assert parse_intent_v1("הסבר וגם תרחישים") == TreasuryIntentV1.EXPLAIN_FX_DECISION
    assert parse_intent_v1("תרחישים וגם ladder") == TreasuryIntentV1.SHOW_SCENARIO_TABLE
    assert parse_intent_v1("policy and hedge") == TreasuryIntentV1.COMPARE_POLICIES


def test_normalization_mixed_case_and_spaces() -> None:
    a = parse_intent_v1("   Explain   the hedge   ")
    b = parse_intent_v1("explain the hedge")
    assert a == b == TreasuryIntentV1.EXPLAIN_FX_DECISION


def test_empty_input_defaults_to_run_advisory() -> None:
    assert parse_intent_v1("") == TreasuryIntentV1.RUN_FX_HEDGE_ADVISORY
    assert parse_intent_v1("   ") == TreasuryIntentV1.RUN_FX_HEDGE_ADVISORY
