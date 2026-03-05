from __future__ import annotations

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
from treasury_copilot_v1 import TreasuryIntentV1
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


def test_fx_advisory_invocation_success_returns_artifacts_and_is_deterministic() -> None:
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

    out1 = run_treasury_copilot_v1(req)
    out2 = run_treasury_copilot_v1(req)

    assert out1.intent == TreasuryIntentV1.RUN_FX_HEDGE_ADVISORY
    assert out1.missing_context == []
    assert "fx_advisory_executed_v1" in out1.warnings
    assert "intent_not_implemented_v1" not in out1.warnings
    assert out1.artifacts is not None
    assert out1.artifacts.advisory_decision is not None
    assert out1.artifacts.explainability is not None
    assert out1.artifacts.report_markdown is not None
    assert out1.artifacts.report_markdown.strip() != ""
    assert "## Snapshot" in out1.artifacts.report_markdown
    assert "## Risk Summary" in out1.artifacts.report_markdown
    assert out1.artifacts == out2.artifacts


def test_fx_advisory_resolution_failure_path_unchanged() -> None:
    req = TreasuryCopilotRequestV1(
        question="תעשה גידור",
        context=CopilotContextV1(
            market_snapshot_id="snap-1",
            scenario_template_id="STANDARD_7",
            policy_template_id="TREASURY_STANDARD_70",
            portfolio_ref="portfolio-1",
        ),
    )

    out = run_treasury_copilot_v1(req)

    assert out.missing_context == []
    assert out.warnings[0] == "resolution_failed_v1"
    assert out.artifacts is None


def test_fx_advisory_missing_context_path_unchanged() -> None:
    req = TreasuryCopilotRequestV1(
        question="תעשה גידור",
        context=CopilotContextV1(
            market_snapshot_id=None,
            scenario_template_id="STANDARD_7",
            policy_template_id="TREASURY_STANDARD_70",
            portfolio_ref=None,
        ),
    )

    out = run_treasury_copilot_v1(req)

    assert out.missing_context == ["market_snapshot_id", "portfolio_ref"]
    assert out.artifacts is None
