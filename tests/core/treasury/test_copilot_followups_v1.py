from __future__ import annotations

import pytest

from core.market_data.artifact_store import put_market_snapshot
from core.market_data.market_snapshot_payload_v0 import Curve
from core.market_data.market_snapshot_payload_v0 import FxRates
from core.market_data.market_snapshot_payload_v0 import InterestRateCurves
from core.market_data.market_snapshot_payload_v0 import MarketConventions
from core.market_data.market_snapshot_payload_v0 import MarketSnapshotPayloadV0
from core.market_data.market_snapshot_payload_v0 import SpotPrices
from core.portfolio.advisory_payload_artifact_store_v1 import put_advisory_payload_artifact_v1
from treasury_copilot_v1 import CopilotContextV1
from treasury_copilot_v1 import TreasuryCopilotRequestV1
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


def _run_success_and_get_decision_ref() -> str:
    market_snapshot_id = put_market_snapshot(_market_payload())
    portfolio_artifact_id = put_advisory_payload_artifact_v1(_payload(market_snapshot_id))

    run_req = TreasuryCopilotRequestV1(
        question="תעשה גידור",
        context=CopilotContextV1(
            market_snapshot_id=market_snapshot_id,
            scenario_template_id="STANDARD_7",
            policy_template_id="TREASURY_STANDARD_70",
            portfolio_ref=f"artifact:{portfolio_artifact_id}",
        ),
    )
    run_out = run_treasury_copilot_v1(run_req)
    assert run_out.audit.as_of_decision_ref is not None
    return run_out.audit.as_of_decision_ref


def test_followup_missing_decision_ref_is_reported() -> None:
    req = TreasuryCopilotRequestV1(
        question="למה המלצת על זה",
        context=CopilotContextV1(
            market_snapshot_id=None,
            scenario_template_id=None,
            policy_template_id=None,
            portfolio_ref=None,
            as_of_decision_ref=None,
        ),
    )

    out = run_treasury_copilot_v1(req)

    assert out.missing_context == ["as_of_decision_ref"]
    assert out.artifacts is None


def test_followup_invalid_ref_returns_deterministic_resolution_failure() -> None:
    req = TreasuryCopilotRequestV1(
        question="למה המלצת על זה",
        context=CopilotContextV1(
            market_snapshot_id=None,
            scenario_template_id=None,
            policy_template_id=None,
            portfolio_ref=None,
            as_of_decision_ref="artifact_bundle:missing",
        ),
    )

    out = run_treasury_copilot_v1(req)

    assert out.missing_context == []
    assert out.artifacts is None
    assert out.warnings[0] == "followup_resolution_failed_v1"
    assert out.warnings[1].startswith("resolution_error:unknown_decision_ref:")


def test_followup_success_loads_ssot_artifacts_without_engine_invocation(monkeypatch: pytest.MonkeyPatch) -> None:
    decision_ref = _run_success_and_get_decision_ref()

    def _boom(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("engine_reinvocation_not_allowed")

    monkeypatch.setattr("treasury_copilot_v1.run_treasury_advisory_v1", _boom)

    req = TreasuryCopilotRequestV1(
        question="למה המלצת על זה",
        context=CopilotContextV1(
            market_snapshot_id=None,
            scenario_template_id=None,
            policy_template_id=None,
            portfolio_ref=None,
            as_of_decision_ref=decision_ref,
        ),
    )

    out1 = run_treasury_copilot_v1(req)
    out2 = run_treasury_copilot_v1(req)

    assert out1.missing_context == []
    assert "read_only_followup_v1" in out1.warnings
    assert out1.artifacts is not None
    assert out1.artifacts.advisory_decision is not None
    assert out1.artifacts.explainability is not None
    assert out1.artifacts.report_markdown is not None
    assert out1.answer_text is not None and out1.answer_text.strip() != ""
    assert out1.artifacts == out2.artifacts
    assert out1.answer_text == out2.answer_text


def test_followup_scenario_and_ladder_are_non_empty_without_engine_invocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decision_ref = _run_success_and_get_decision_ref()

    def _boom(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("engine_reinvocation_not_allowed")

    monkeypatch.setattr("treasury_copilot_v1.run_treasury_advisory_v1", _boom)

    scenario_req = TreasuryCopilotRequestV1(
        question="תראה לי טבלת תרחישים",
        context=CopilotContextV1(
            market_snapshot_id=None,
            scenario_template_id=None,
            policy_template_id=None,
            portfolio_ref=None,
            as_of_decision_ref=decision_ref,
        ),
    )
    ladder_req = TreasuryCopilotRequestV1(
        question="תראה לי סולם גידור",
        context=CopilotContextV1(
            market_snapshot_id=None,
            scenario_template_id=None,
            policy_template_id=None,
            portfolio_ref=None,
            as_of_decision_ref=decision_ref,
        ),
    )

    scenario_out = run_treasury_copilot_v1(scenario_req)
    ladder_out = run_treasury_copilot_v1(ladder_req)

    assert "read_only_followup_v1" in scenario_out.warnings
    assert "read_only_followup_v1" in ladder_out.warnings
    assert scenario_out.answer_text is not None and scenario_out.answer_text.strip() != ""
    assert ladder_out.answer_text is not None and ladder_out.answer_text.strip() != ""
