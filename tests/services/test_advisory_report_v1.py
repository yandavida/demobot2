from __future__ import annotations

import datetime
from decimal import Decimal

from core.pricing.fx.types import FxMarketSnapshot
from core.risk.scenario_spec import ScenarioSpec
from core.services.advisory_read_model_v1 import run_treasury_advisory_v1
from core.services.advisory_report_v1 import render_advisory_report_markdown_v1
from core.services.hedge_policy_constraints_v1 import HedgePolicyV1
from core.services.rolling_hedge_ladder_v1 import RollingHedgeLadderConfigV1
from core.services.rolling_hedge_ladder_v1 import compute_rolling_hedge_ladder_v1


def _base_snapshot() -> FxMarketSnapshot:
    return FxMarketSnapshot(
        as_of_ts=datetime.datetime(
            2026,
            3,
            5,
            12,
            0,
            0,
            tzinfo=datetime.timezone(datetime.timedelta(hours=2)),
        ),
        spot_rate=3.70,
        df_domestic=0.997,
        df_foreign=0.996,
        domestic_currency="ILS",
    )


def _scenario_spec() -> ScenarioSpec:
    return ScenarioSpec(
        schema_version=1,
        spot_shocks=(Decimal("-0.07"), Decimal("0.0"), Decimal("0.07")),
        df_domestic_shocks=(Decimal("0.0"),),
        df_foreign_shocks=(Decimal("0.0"),),
    )


def _payload() -> dict:
    return {
        "contract_version": "v1",
        "company_id": "g11-sim1-usdils-importer",
        "snapshot_id": "snap-usdils-20260305",
        "scenario_template_id": "usdils_spot_custom_5pt",
        "exposures": [
            {
                "currency_pair": "USD/ILS",
                "direction": "payable",
                "notional": "4200000",
                "maturity_date": "2026-03-25",
                "hedge_ratio": "0.35",
            },
            {
                "currency_pair": "USD/ILS",
                "direction": "payable",
                "notional": "3000000",
                "maturity_date": "2026-04-29",
                "hedge_ratio": "0.35",
            },
            {
                "currency_pair": "USD/ILS",
                "direction": "payable",
                "notional": "1800000",
                "maturity_date": "2026-07-03",
                "hedge_ratio": "0.35",
            },
        ],
    }


def _build_decision_and_ladder() -> tuple:
    payload = _payload()
    snapshot = _base_snapshot()
    spec = _scenario_spec()

    decision = run_treasury_advisory_v1(
        payload,
        base_snapshot=snapshot,
        scenario_spec=spec,
        target_worst_loss_domestic=250000.0,
    )

    ladder = compute_rolling_hedge_ladder_v1(
        payload,
        base_snapshot=snapshot,
        scenario_spec=spec,
        config=RollingHedgeLadderConfigV1(
            buckets_days=(30, 60, 90, 180),
            roll_frequency_days=30,
            target_worst_loss_total_domestic=250000.0,
            as_of_date="2026-03-05",
            policy=HedgePolicyV1(
                policy_id="sim1-policy",
                min_hedge_ratio=0.20,
                max_hedge_ratio=0.70,
                rounding_lot_notional=10000.0,
                allow_overhedge=False,
            ),
        ),
    )
    return payload, decision, ladder


def test_report_markdown_v1_is_deterministic_and_has_required_sections() -> None:
    payload, decision, ladder = _build_decision_and_ladder()

    report_a = render_advisory_report_markdown_v1(
        company_id=payload["company_id"],
        as_of_date="2026-03-05",
        pair="USD/ILS",
        decision=decision,
        risk_summary=decision.risk_summary,
        ladder=ladder,
    )
    report_b = render_advisory_report_markdown_v1(
        company_id=payload["company_id"],
        as_of_date="2026-03-05",
        pair="USD/ILS",
        decision=decision,
        risk_summary=decision.risk_summary,
        ladder=ladder,
    )

    assert report_a == report_b

    required_headings = [
        "# Treasury Hedge Advisory — v1",
        "## Snapshot",
        "## Executive Takeaway",
        "## Exposure Summary",
        "## Risk Summary",
        "## Scenario P&L Table",
        "## Hedge Trade Ticket",
        "## Rolling Hedge Ladder",
        "## Audit",
    ]
    for heading in required_headings:
        assert report_a.count(heading) == 1

    assert payload["company_id"] in report_a
    assert "USD/ILS" in report_a
    assert "current ratio:" in report_a
    assert "recommended ratio (post policy):" in report_a
    assert "worst loss domestic:" in report_a
    assert "delta aggregate:" in report_a
    assert "per 1%" in report_a
    assert "Coverage uplift:" in report_a
    assert "Tail scenario:" in report_a
    assert "Objective:" in report_a
    assert "- Action:" in report_a

    table_lines = [line for line in report_a.splitlines() if line.startswith("|")]
    assert len(table_lines) >= 3

    assert "| 0-30 |" in report_a or "| 31-60 |" in report_a or "| 91-180 |" in report_a


def test_report_ratio_and_ticket_are_policy_consistent() -> None:
    payload, decision, ladder = _build_decision_and_ladder()

    report = render_advisory_report_markdown_v1(
        company_id=payload["company_id"],
        as_of_date="2026-03-05",
        pair="USD/ILS",
        decision=decision,
        risk_summary=decision.risk_summary,
        ladder=ladder,
    )

    assert "- Recommended hedge notional: 6,300,000.00 USD" in report
    assert "- recommended ratio (post policy): 0.700000" in report
    assert "- Summary: BUY USD FWD +3,150,000.00 (raise hedge to 0.700000)" in report

    ladder_ratio_lines = [
        line for line in report.splitlines() if line.startswith("| 0-30 |") or line.startswith("| 31-60 |") or line.startswith("| 91-180 |")
    ]
    assert ladder_ratio_lines
    for line in ladder_ratio_lines:
        assert "| 0.700000 |" in line

    if "MAX_HEDGE_RATIO" in report:
        post_line = next(line for line in report.splitlines() if line.startswith("- recommended ratio (post policy): "))
        ratio = float(post_line.split(":", 1)[1].strip())
        assert ratio <= 0.70


def test_report_markdown_v1_ladder_none_prints_na() -> None:
    payload, decision, _ = _build_decision_and_ladder()

    report = render_advisory_report_markdown_v1(
        company_id=payload["company_id"],
        as_of_date="2026-03-05",
        pair="USD/ILS",
        decision=decision,
        risk_summary=decision.risk_summary,
        ladder=None,
    )

    assert "## Rolling Hedge Ladder" in report
    assert "N/A" in report
