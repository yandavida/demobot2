from __future__ import annotations

from dataclasses import fields

from core.market_data.artifact_store import put_market_snapshot
from core.market_data.market_snapshot_payload_v0 import Curve
from core.market_data.market_snapshot_payload_v0 import FxRates
from core.market_data.market_snapshot_payload_v0 import InterestRateCurves
from core.market_data.market_snapshot_payload_v0 import MarketConventions
from core.market_data.market_snapshot_payload_v0 import MarketSnapshotPayloadV0
from core.market_data.market_snapshot_payload_v0 import SpotPrices
from core.portfolio.advisory_payload_artifact_store_v1 import put_advisory_payload_artifact_v1
from treasury_copilot_v1 import CopilotArtifactsV1
from treasury_copilot_v1 import CopilotAuditV1
from treasury_copilot_v1 import CopilotContextV1
from treasury_copilot_v1 import TreasuryCopilotRequestV1
from treasury_copilot_v1 import TreasuryCopilotResponseV1
from treasury_copilot_v1 import run_treasury_copilot_v1


def _market_payload() -> MarketSnapshotPayloadV0:
    return MarketSnapshotPayloadV0(
        fx_rates=FxRates(base_ccy="USD", quotes={"ILS": 3.7}),
        spots=SpotPrices(prices={"USD/ILS": 3.7}, currency={"USD/ILS": "ILS"}),
        curves=InterestRateCurves(
            curves={
                "ILS": Curve(day_count="ACT/365", compounding="annual", zero_rates={"365D": 0.04}),
                "USD": Curve(day_count="ACT/365", compounding="annual", zero_rates={"365D": 0.03}),
            }
        ),
        conventions=MarketConventions(calendar="IL", day_count_default="ACT/365", spot_lag=2),
    )


def _payload(snapshot_id: str) -> dict:
    return {
        "contract_version": "v1",
        "company_id": "treasury-demo",
        "snapshot_id": snapshot_id,
        "scenario_template_id": "usdils_spot_pm5",
        "exposures": [
            {
                "currency_pair": "USD/ILS",
                "direction": "receivable",
                "notional": "3000000",
                "maturity_date": "2026-06-02",
                "hedge_ratio": "0.60",
            }
        ],
    }


def _run_success() -> TreasuryCopilotResponseV1:
    market_snapshot_id = put_market_snapshot(_market_payload())
    portfolio_artifact_id = put_advisory_payload_artifact_v1(_payload(market_snapshot_id))
    req = TreasuryCopilotRequestV1(
        question="תעשה גידור",
        context=CopilotContextV1(
            market_snapshot_id=market_snapshot_id,
            scenario_template_id="STANDARD_7",
            policy_template_id="TREASURY_STANDARD_70",
            portfolio_ref=f"artifact:{portfolio_artifact_id}",
        ),
    )
    return run_treasury_copilot_v1(req)


def test_context_request_response_audit_and_artifacts_field_order_is_frozen() -> None:
    assert [f.name for f in fields(CopilotContextV1)] == [
        "market_snapshot_id",
        "scenario_template_id",
        "policy_template_id",
        "portfolio_ref",
        "as_of_decision_ref",
    ]
    assert [f.name for f in fields(TreasuryCopilotRequestV1)] == [
        "question",
        "context",
        "response_style",
    ]
    assert [f.name for f in fields(TreasuryCopilotResponseV1)] == [
        "intent",
        "answer_text",
        "artifacts",
        "warnings",
        "missing_context",
        "audit",
    ]
    assert [f.name for f in fields(CopilotAuditV1)] == [
        "intent",
        "normalized_question",
        "as_of_decision_ref",
    ]
    assert [f.name for f in fields(CopilotArtifactsV1)] == [
        "advisory_decision",
        "explainability",
        "report_markdown",
        "scenario_table_markdown",
        "ladder_table_markdown",
    ]


def test_warning_codes_are_frozen_across_canonical_router_flows() -> None:
    success = _run_success()
    assert success.warnings == ["fx_advisory_executed_v1"]
    assert success.audit.as_of_decision_ref is not None

    followup_ok = run_treasury_copilot_v1(
        TreasuryCopilotRequestV1(
            question="למה המלצת על זה",
            context=CopilotContextV1(
                market_snapshot_id=None,
                scenario_template_id=None,
                policy_template_id=None,
                portfolio_ref=None,
                as_of_decision_ref=success.audit.as_of_decision_ref,
            ),
        )
    )
    assert followup_ok.warnings == ["read_only_followup_v1"]

    run_resolution_fail = run_treasury_copilot_v1(
        TreasuryCopilotRequestV1(
            question="תעשה גידור",
            context=CopilotContextV1(
                market_snapshot_id="snap-1",
                scenario_template_id="STANDARD_7",
                policy_template_id="TREASURY_STANDARD_70",
                portfolio_ref="portfolio-1",
            ),
        )
    )
    assert run_resolution_fail.warnings[0] == "resolution_failed_v1"

    followup_resolution_fail = run_treasury_copilot_v1(
        TreasuryCopilotRequestV1(
            question="למה המלצת על זה",
            context=CopilotContextV1(
                market_snapshot_id=None,
                scenario_template_id=None,
                policy_template_id=None,
                portfolio_ref=None,
                as_of_decision_ref="artifact_bundle:missing",
            ),
        )
    )
    assert followup_resolution_fail.warnings[0] == "followup_resolution_failed_v1"

    allowed = {
        "fx_advisory_executed_v1",
        "read_only_followup_v1",
        "resolution_failed_v1",
        "followup_resolution_failed_v1",
    }
    seen = {
        success.warnings[0],
        followup_ok.warnings[0],
        run_resolution_fail.warnings[0],
        followup_resolution_fail.warnings[0],
    }
    assert seen == allowed
