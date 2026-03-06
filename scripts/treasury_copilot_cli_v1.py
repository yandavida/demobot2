from __future__ import annotations

import argparse
import json
import sys

from treasury_copilot_v1 import CopilotContextV1
from treasury_copilot_v1 import TreasuryCopilotRequestV1
from treasury_copilot_v1 import run_treasury_copilot_v1


EXIT_OK = 0
EXIT_MISSING_CONTEXT = 2
EXIT_RESOLUTION_FAILED = 3


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m scripts.treasury_copilot_cli_v1")
    parser.add_argument("--question", required=True)
    parser.add_argument("--market-snapshot-id")
    parser.add_argument("--scenario-template-id")
    parser.add_argument("--policy-template-id")
    parser.add_argument("--portfolio-ref")
    parser.add_argument("--as-of-decision-ref")
    parser.add_argument("--print-report", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def _build_context(args: argparse.Namespace) -> CopilotContextV1:
    return CopilotContextV1(
        market_snapshot_id=args.market_snapshot_id,
        scenario_template_id=args.scenario_template_id,
        policy_template_id=args.policy_template_id,
        portfolio_ref=args.portfolio_ref,
        as_of_decision_ref=args.as_of_decision_ref,
    )


def _validate_mode_requirements(args: argparse.Namespace) -> tuple[bool, list[str]]:
    if args.as_of_decision_ref:
        return True, []

    missing: list[str] = []
    if not args.market_snapshot_id:
        missing.append("market_snapshot_id")
    if not args.scenario_template_id:
        missing.append("scenario_template_id")
    if not args.policy_template_id:
        missing.append("policy_template_id")
    if not args.portfolio_ref:
        missing.append("portfolio_ref")
    return False, missing


def _print_text_output(resp, *, print_report: bool) -> None:
    print(resp.answer_text or "")
    print(f"warnings={','.join(resp.warnings)}")
    if resp.audit.as_of_decision_ref:
        print(f"decision_ref={resp.audit.as_of_decision_ref}")
    if print_report and resp.artifacts is not None and resp.artifacts.report_markdown:
        print(resp.artifacts.report_markdown)


def _print_json_output(resp) -> None:
    payload = {
        "intent": str(getattr(resp.intent, "value", resp.intent)),
        "warnings": list(resp.warnings),
        "decision_ref": resp.audit.as_of_decision_ref,
        "answer_text": resp.answer_text,
    }
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def _exit_code_for_response(resp) -> int:
    if resp.missing_context:
        return EXIT_MISSING_CONTEXT
    if "resolution_failed_v1" in resp.warnings or "followup_resolution_failed_v1" in resp.warnings:
        return EXIT_RESOLUTION_FAILED
    if "fx_advisory_executed_v1" in resp.warnings or "read_only_followup_v1" in resp.warnings:
        return EXIT_OK
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    is_followup_mode, missing = _validate_mode_requirements(args)
    if missing:
        print("missing_required_args=" + ",".join(missing))
        return EXIT_MISSING_CONTEXT

    if is_followup_mode:
        context = CopilotContextV1(
            market_snapshot_id=None,
            scenario_template_id=None,
            policy_template_id=None,
            portfolio_ref=None,
            as_of_decision_ref=args.as_of_decision_ref,
        )
    else:
        context = _build_context(args)

    req = TreasuryCopilotRequestV1(question=args.question, context=context)
    resp = run_treasury_copilot_v1(req)

    if args.json:
        _print_json_output(resp)
    else:
        _print_text_output(resp, print_report=args.print_report)

    return _exit_code_for_response(resp)


if __name__ == "__main__":
    raise SystemExit(main())
