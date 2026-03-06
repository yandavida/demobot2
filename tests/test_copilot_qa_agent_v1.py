from __future__ import annotations

import json

from scripts import copilot_qa_agent_v1 as qa


def _result(returncode: int, stdout: str = "", stderr: str = "", details: str = "ok") -> qa.CompletedStepResult:
    return qa.CompletedStepResult(
        status=qa.PASS if returncode == 0 else qa.FAIL,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        details=details,
    )


def test_human_summary_contains_all_sections_in_order() -> None:
    def fake_runner(cmd: list[str]) -> qa.CompletedStepResult:
        if cmd[:2] == ["ruff", "check"]:
            return _result(0, details="ruff_ok")
        if cmd[:2] == ["pytest", "-q"]:
            return _result(0, details="pytest_ok")
        if "תעשה גידור לחשיפה הזאת" in cmd:
            payload = {
                "intent": "RUN_FX_HEDGE_ADVISORY",
                "warnings": ["fx_advisory_executed_v1"],
                "decision_ref": "artifact_bundle:abc",
                "answer_text": "ok",
            }
            return _result(0, stdout=json.dumps(payload, ensure_ascii=False))
        payload = {
            "intent": "EXPLAIN_FX_DECISION",
            "warnings": ["read_only_followup_v1"],
            "decision_ref": "artifact_bundle:abc",
            "answer_text": "ok",
        }
        return _result(0, stdout=json.dumps(payload, ensure_ascii=False))

    summary = qa.run_qa_flow_v1(
        market_snapshot_id="s",
        scenario_template_id="sc",
        policy_template_id="p",
        portfolio_ref="artifact:x",
        run_ruff=True,
        run_targeted_pytest=True,
        run_determinism_check=True,
        print_report=False,
        runner=fake_runner,
        path_exists=lambda _p: True,
    )
    text = qa._build_human_summary_v1(summary)

    expected_order = [
        "COPILOT QA STATUS:",
        "[1] Ruff",
        "[2] Targeted Pytest",
        "[3] CLI RUN",
        "[4] Follow-up Explain",
        "[5] Follow-up Scenario Table",
        "[6] Follow-up Hedge Ladder",
        "[7] Determinism",
        "Final Verdict:",
    ]
    positions = [text.index(token) for token in expected_order]
    assert positions == sorted(positions)


def test_json_summary_has_stable_keys_and_values() -> None:
    summary = {
        "overall_status": "FAIL",
        "ruff": {"status": "PASS", "details": "ok"},
        "targeted_pytest": {"status": "SKIPPED", "details": "disabled"},
        "cli_run": {"status": "FAIL", "warnings": "", "decision_ref": "", "details": "bad"},
        "followup_explain": {"status": "SKIPPED", "warnings": "", "details": "skip"},
        "followup_scenario_table": {"status": "PASS", "warnings": "read_only_followup_v1", "details": "ok"},
        "followup_hedge_ladder": {"status": "PASS", "warnings": "read_only_followup_v1", "details": "ok"},
        "determinism": {"status": "SKIPPED", "details": "disabled"},
    }

    text = qa._build_json_summary_v1(summary)
    payload = json.loads(text)

    assert list(payload.keys()) == [
        "overall_status",
        "ruff",
        "targeted_pytest",
        "cli_run",
        "followup_explain",
        "followup_scenario_table",
        "followup_hedge_ladder",
        "determinism",
    ]
    assert payload["overall_status"] == "FAIL"
    assert payload["cli_run"]["status"] == "FAIL"


def test_determinism_ignores_decision_ref_difference() -> None:
    first = {
        "intent": "RUN_FX_HEDGE_ADVISORY",
        "warnings": ["fx_advisory_executed_v1"],
        "decision_ref": "artifact_bundle:1",
        "answer_text": "stable",
    }
    second = {
        "intent": "RUN_FX_HEDGE_ADVISORY",
        "warnings": ["fx_advisory_executed_v1"],
        "decision_ref": "artifact_bundle:2",
        "answer_text": "stable",
    }

    out = qa._determinism_stage_v1(first, second)
    assert out["status"] == qa.PASS


def test_cli_run_failure_skips_followups_and_fails_overall() -> None:
    def fake_runner(cmd: list[str]) -> qa.CompletedStepResult:
        if cmd[:2] == ["ruff", "check"]:
            return _result(0)
        if cmd[:2] == ["pytest", "-q"]:
            return _result(0)
        if "תעשה גידור לחשיפה הזאת" in cmd:
            return _result(3, stdout="{\"warnings\":[\"resolution_failed_v1\"]}", details="run_failed")
        return _result(0)

    summary = qa.run_qa_flow_v1(
        market_snapshot_id="s",
        scenario_template_id="sc",
        policy_template_id="p",
        portfolio_ref="artifact:x",
        run_ruff=True,
        run_targeted_pytest=True,
        run_determinism_check=True,
        print_report=False,
        runner=fake_runner,
        path_exists=lambda _p: True,
    )

    assert summary["cli_run"]["status"] == qa.FAIL
    assert summary["followup_explain"]["status"] == qa.SKIPPED
    assert summary["followup_scenario_table"]["status"] == qa.SKIPPED
    assert summary["followup_hedge_ladder"]["status"] == qa.SKIPPED
    assert summary["overall_status"] == qa.FAIL
