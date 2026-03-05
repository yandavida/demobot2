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
from core.risk.scenario_spec import ScenarioSpec
from core.treasury.copilot_resolution_v1 import CopilotResolutionError
from core.treasury.copilot_resolution_v1 import resolve_copilot_inputs_fx_v1
from core.treasury.copilot_resolution_v1 import resolve_policy_inputs_v1
from core.treasury.copilot_resolution_v1 import resolve_scenario_spec_v1
from treasury_copilot_v1 import CopilotContextV1
from treasury_copilot_v1 import TreasuryCopilotRequestV1
from treasury_copilot_v1 import run_treasury_copilot_v1


def _payload() -> dict:
    return {
        "contract_version": "v1",
        "company_id": "treasury-demo",
        "snapshot_id": "snap-usdils-20260304",
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


def test_resolve_scenario_spec_from_catalog() -> None:
    spec = resolve_scenario_spec_v1("STANDARD_7")

    assert isinstance(spec, ScenarioSpec)
    assert tuple(float(x) for x in spec.spot_shocks) == (-0.07, 0.0, 0.07)


def test_resolve_policy_inputs_from_catalog() -> None:
    policy_template, target = resolve_policy_inputs_v1("TREASURY_STANDARD_70")

    assert getattr(policy_template, "template_id") == "TREASURY_STANDARD_70"
    assert isinstance(target, float)


def test_unknown_ids_raise_hard_failures() -> None:
    with pytest.raises(Exception, match="unknown_scenario_template_id"):
        resolve_scenario_spec_v1("NOPE")

    with pytest.raises(Exception, match="unknown_policy_template_id"):
        resolve_policy_inputs_v1("NOPE")


def test_unified_resolver_wraps_portfolio_resolution_error() -> None:
    context = CopilotContextV1(
        market_snapshot_id="snap-1",
        scenario_template_id="STANDARD_7",
        policy_template_id="TREASURY_STANDARD_70",
        portfolio_ref="portfolio-1",
    )

    with pytest.raises(CopilotResolutionError, match="portfolio_resolution_failed:unsupported_portfolio_ref_format"):
        resolve_copilot_inputs_fx_v1(context)


def test_router_fx_sufficient_context_resolution_failure_warning() -> None:
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
    assert out.warnings[1].startswith("resolution_error:portfolio_resolution_failed:")


def test_router_fx_sufficient_context_resolution_ready_warning() -> None:
    market_snapshot_id = put_market_snapshot(_market_payload())
    portfolio_artifact_id = put_advisory_payload_artifact_v1(_payload())

    req = TreasuryCopilotRequestV1(
        question="תעשה גידור",
        context=CopilotContextV1(
            market_snapshot_id=market_snapshot_id,
            scenario_template_id="STANDARD_7",
            policy_template_id="TREASURY_STANDARD_70",
            portfolio_ref=f"artifact:{portfolio_artifact_id}",
        ),
    )

    out = run_treasury_copilot_v1(req)

    assert out.missing_context == []
    assert out.warnings == ["resolution_ready_v1", "intent_not_implemented_v1"]
