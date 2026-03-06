from __future__ import annotations

"""Deterministic Treasury Copilot QA runner V1.

Example invocation:
python -m scripts.copilot_qa_agent_v1 \
  --market-snapshot-id SNAPSHOT_001 \
  --scenario-template-id STANDARD_7 \
  --policy-template-id TREASURY_STANDARD_70 \
  --portfolio-ref artifact:PORTFOLIO_001

Follow-up flow (read-only):
1) RUN generates a decision_ref
2) EXPLAIN / SCENARIO TABLE / HEDGE LADDER load from artifact bundle using that decision_ref
"""

import argparse
from dataclasses import dataclass
import json
import os
import subprocess
import sys
from typing import Callable


PASS = "PASS"
FAIL = "FAIL"
SKIPPED = "SKIPPED"


@dataclass(frozen=True)
class CompletedStepResult:
    status: str
    returncode: int
    stdout: str
    stderr: str
    details: str


def _parse_bool_flag(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError("expected true/false")


def _compact_output(stdout: str, stderr: str) -> str:
    for source in (stdout, stderr):
        lines = [line.strip() for line in source.splitlines() if line.strip()]
        if lines:
            return lines[-1]
    return "no output"


def _build_env() -> dict[str, str]:
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    paths = ["src", "."]
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def run_subprocess_v1(cmd: list[str]) -> CompletedStepResult:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=_build_env(),
        check=False,
    )
    details = _compact_output(result.stdout, result.stderr)
    return CompletedStepResult(
        status=PASS if result.returncode == 0 else FAIL,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        details=details,
    )


def _parse_cli_json(stdout: str) -> dict | None:
    text = stdout.strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _warning_contains(payload: dict, expected: str) -> bool:
    warnings = payload.get("warnings")
    return isinstance(warnings, list) and expected in [str(item) for item in warnings]


def _build_targeted_pytest_file_list(path_exists: Callable[[str], bool]) -> tuple[list[str], list[str]]:
    ordered = [
        "test_treasury_copilot_v1_router.py",
        "tests/core/treasury/test_copilot_resolution_v1.py",
        "tests/core/treasury/test_copilot_invocation_v1.py",
        "tests/core/treasury/test_copilot_followups_v1.py",
        "test_treasury_copilot_renderer_v1.py",
        "tests/test_treasury_copilot_cli_v1.py",
        "tests/core/treasury/test_treasury_copilot_contract_freeze_v1.py",
        "tests/core/treasury/test_copilot_artifact_bundle_schema_v1.py",
    ]
    present: list[str] = []
    missing: list[str] = []
    for file_path in ordered:
        if path_exists(file_path):
            present.append(file_path)
        else:
            missing.append(file_path)
    return present, missing


def _build_human_summary_v1(summary: dict) -> str:
    lines = [f"COPILOT QA STATUS: {summary['overall_status']}", ""]

    ordered_sections = [
        ("[1] Ruff", "ruff", False),
        ("[2] Targeted Pytest", "targeted_pytest", False),
        ("[3] CLI RUN", "cli_run", True),
        ("[4] Follow-up Explain", "followup_explain", True),
        ("[5] Follow-up Scenario Table", "followup_scenario_table", True),
        ("[6] Follow-up Hedge Ladder", "followup_hedge_ladder", True),
        ("[7] Determinism", "determinism", False),
    ]

    for title, key, include_meta in ordered_sections:
        section = summary[key]
        lines.append(title)
        lines.append(f"Status: {section['status']}")
        if include_meta:
            lines.append(f"Warnings: {section.get('warnings', '')}")
            if key == "cli_run":
                lines.append(f"Decision Ref: {section.get('decision_ref', '')}")
        lines.append(f"Details: {section.get('details', '')}")
        lines.append("")

    lines.append("Final Verdict:")
    lines.append(summary["overall_status"])
    return "\n".join(lines)


def _build_json_summary_v1(summary: dict) -> str:
    payload = {
        "overall_status": summary["overall_status"],
        "ruff": summary["ruff"],
        "targeted_pytest": summary["targeted_pytest"],
        "cli_run": summary["cli_run"],
        "followup_explain": summary["followup_explain"],
        "followup_scenario_table": summary["followup_scenario_table"],
        "followup_hedge_ladder": summary["followup_hedge_ladder"],
        "determinism": summary["determinism"],
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=False)


def _determinism_stage_v1(first_payload: dict | None, second_payload: dict | None) -> dict:
    if first_payload is None or second_payload is None:
        return {
            "status": FAIL,
            "details": "missing_cli_json_for_determinism",
        }

    mismatches: list[str] = []
    for key in ("intent", "warnings", "answer_text"):
        if first_payload.get(key) != second_payload.get(key):
            mismatches.append(key)

    if mismatches:
        return {
            "status": FAIL,
            "details": "mismatch_fields=" + ",".join(mismatches),
        }

    return {
        "status": PASS,
        "details": "intent,warnings,answer_text are deterministic",
    }


def run_qa_flow_v1(
    *,
    market_snapshot_id: str,
    scenario_template_id: str,
    policy_template_id: str,
    portfolio_ref: str,
    run_ruff: bool,
    run_targeted_pytest: bool,
    run_determinism_check: bool,
    print_report: bool,
    runner: Callable[[list[str]], CompletedStepResult],
    path_exists: Callable[[str], bool],
) -> dict:
    summary = {
        "overall_status": PASS,
        "ruff": {"status": SKIPPED, "details": "disabled_by_flag"},
        "targeted_pytest": {"status": SKIPPED, "details": "disabled_by_flag"},
        "cli_run": {"status": SKIPPED, "warnings": "", "decision_ref": "", "details": "not_run"},
        "followup_explain": {"status": SKIPPED, "warnings": "", "details": "not_run"},
        "followup_scenario_table": {"status": SKIPPED, "warnings": "", "details": "not_run"},
        "followup_hedge_ladder": {"status": SKIPPED, "warnings": "", "details": "not_run"},
        "determinism": {"status": SKIPPED, "details": "disabled_by_flag"},
    }

    if run_ruff:
        ruff_step = runner(["ruff", "check", "."])
        summary["ruff"] = {
            "status": ruff_step.status,
            "details": ruff_step.details,
        }

    if run_targeted_pytest:
        present, missing = _build_targeted_pytest_file_list(path_exists)
        if not present:
            summary["targeted_pytest"] = {
                "status": SKIPPED,
                "details": "no_targeted_pytest_files_found",
            }
        else:
            pytest_step = runner(["pytest", "-q", *present])
            detail = pytest_step.details
            if missing:
                detail = detail + " | skipped_missing=" + ",".join(missing)
            summary["targeted_pytest"] = {
                "status": pytest_step.status,
                "details": detail,
            }

    run_cmd = [
        sys.executable,
        "-m",
        "scripts.treasury_copilot_cli_v1",
        "--question",
        "תעשה גידור לחשיפה הזאת",
        "--market-snapshot-id",
        market_snapshot_id,
        "--scenario-template-id",
        scenario_template_id,
        "--policy-template-id",
        policy_template_id,
        "--portfolio-ref",
        portfolio_ref,
        "--json",
    ]
    if print_report:
        run_cmd.append("--print-report")

    run_step = runner(run_cmd)
    run_payload = _parse_cli_json(run_step.stdout)
    decision_ref = ""
    run_status = FAIL
    run_details = run_step.details
    run_warnings = ""

    if run_step.returncode != 0:
        run_status = FAIL
        run_details = f"exit_code={run_step.returncode}; {run_step.details}"
    elif run_payload is None:
        run_status = FAIL
        run_details = "invalid_cli_json"
    else:
        run_warnings_list = run_payload.get("warnings")
        run_warnings = "" if not isinstance(run_warnings_list, list) else ",".join(str(x) for x in run_warnings_list)
        decision_ref_raw = run_payload.get("decision_ref")
        answer_text = run_payload.get("answer_text")
        decision_ref = "" if not isinstance(decision_ref_raw, str) else decision_ref_raw
        if not _warning_contains(run_payload, "fx_advisory_executed_v1"):
            run_status = FAIL
            run_details = "missing_warning:fx_advisory_executed_v1"
        elif not decision_ref.startswith("artifact_bundle:"):
            run_status = FAIL
            run_details = "invalid_decision_ref"
        elif not isinstance(answer_text, str) or not answer_text.strip():
            run_status = FAIL
            run_details = "empty_answer_text"
        else:
            run_status = PASS
            run_details = "cli_run_smoke_passed"

    summary["cli_run"] = {
        "status": run_status,
        "warnings": run_warnings,
        "decision_ref": decision_ref,
        "details": run_details,
    }

    followup_specs = [
        ("followup_explain", "תסביר לי למה"),
        ("followup_scenario_table", "תראה לי טבלת תרחישים"),
        ("followup_hedge_ladder", "תראה לי סולם גידור"),
    ]

    if run_status != PASS:
        for key, _question in followup_specs:
            summary[key] = {
                "status": SKIPPED,
                "warnings": "",
                "details": "skipped_due_to_cli_run_failure",
            }
        summary["determinism"] = {
            "status": SKIPPED if run_determinism_check else SKIPPED,
            "details": "skipped_due_to_cli_run_failure",
        }
    else:
        for key, question in followup_specs:
            followup_cmd = [
                sys.executable,
                "-m",
                "scripts.treasury_copilot_cli_v1",
                "--question",
                question,
                "--as-of-decision-ref",
                decision_ref,
                "--json",
            ]
            step = runner(followup_cmd)
            payload = _parse_cli_json(step.stdout)
            if step.returncode != 0:
                summary[key] = {
                    "status": FAIL,
                    "warnings": "",
                    "details": f"exit_code={step.returncode}; {step.details}",
                }
                continue
            if payload is None:
                summary[key] = {
                    "status": FAIL,
                    "warnings": "",
                    "details": "invalid_cli_json",
                }
                continue
            warnings_list = payload.get("warnings")
            warnings_text = "" if not isinstance(warnings_list, list) else ",".join(str(x) for x in warnings_list)
            answer_text = payload.get("answer_text")
            if not _warning_contains(payload, "read_only_followup_v1"):
                summary[key] = {
                    "status": FAIL,
                    "warnings": warnings_text,
                    "details": "missing_warning:read_only_followup_v1",
                }
            elif not isinstance(answer_text, str) or not answer_text.strip():
                summary[key] = {
                    "status": FAIL,
                    "warnings": warnings_text,
                    "details": "empty_answer_text",
                }
            else:
                summary[key] = {
                    "status": PASS,
                    "warnings": warnings_text,
                    "details": "followup_smoke_passed",
                }

        if run_determinism_check:
            second_run_step = runner(run_cmd)
            second_payload = _parse_cli_json(second_run_step.stdout)
            if second_run_step.returncode != 0:
                summary["determinism"] = {
                    "status": FAIL,
                    "details": f"second_run_exit_code={second_run_step.returncode}",
                }
            else:
                summary["determinism"] = _determinism_stage_v1(run_payload, second_payload)
        else:
            summary["determinism"] = {
                "status": SKIPPED,
                "details": "disabled_by_flag",
            }

    statuses = [
        summary["ruff"]["status"],
        summary["targeted_pytest"]["status"],
        summary["cli_run"]["status"],
        summary["followup_explain"]["status"],
        summary["followup_scenario_table"]["status"],
        summary["followup_hedge_ladder"]["status"],
        summary["determinism"]["status"],
    ]
    if FAIL in statuses:
        summary["overall_status"] = FAIL
    else:
        summary["overall_status"] = PASS

    return summary


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m scripts.copilot_qa_agent_v1")
    parser.add_argument("--market-snapshot-id", required=True)
    parser.add_argument("--scenario-template-id", required=True)
    parser.add_argument("--policy-template-id", required=True)
    parser.add_argument("--portfolio-ref", required=True)

    parser.add_argument("--run-ruff", type=_parse_bool_flag, default=True)
    parser.add_argument("--run-targeted-pytest", type=_parse_bool_flag, default=True)
    parser.add_argument("--run-determinism-check", type=_parse_bool_flag, default=True)
    parser.add_argument("--print-report", action="store_true", default=False)
    parser.add_argument("--json", action="store_true", default=False)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    summary = run_qa_flow_v1(
        market_snapshot_id=args.market_snapshot_id,
        scenario_template_id=args.scenario_template_id,
        policy_template_id=args.policy_template_id,
        portfolio_ref=args.portfolio_ref,
        run_ruff=bool(args.run_ruff),
        run_targeted_pytest=bool(args.run_targeted_pytest),
        run_determinism_check=bool(args.run_determinism_check),
        print_report=bool(args.print_report),
        runner=run_subprocess_v1,
        path_exists=os.path.exists,
    )

    print(_build_human_summary_v1(summary))
    if args.json:
        print(_build_json_summary_v1(summary))

    return 0 if summary["overall_status"] == PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
