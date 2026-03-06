from __future__ import annotations

import json

from core.market_data.artifact_store import put_market_snapshot
from core.market_data.market_snapshot_payload_v0 import Curve
from core.market_data.market_snapshot_payload_v0 import FxRates
from core.market_data.market_snapshot_payload_v0 import InterestRateCurves
from core.market_data.market_snapshot_payload_v0 import MarketConventions
from core.market_data.market_snapshot_payload_v0 import MarketSnapshotPayloadV0
from core.market_data.market_snapshot_payload_v0 import SpotPrices
from core.portfolio.advisory_payload_artifact_store_v1 import put_advisory_payload_artifact_v1
from core.treasury.copilot_artifact_bundle_store_v1 import get_copilot_artifact_bundle_v1
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


def _run_success() -> str:
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
    out = run_treasury_copilot_v1(req)
    assert out.audit.as_of_decision_ref is not None
    return out.audit.as_of_decision_ref


def _artifact_id_from_ref(decision_ref: str) -> str:
    prefix = "artifact_bundle:"
    assert decision_ref.startswith(prefix)
    return decision_ref[len(prefix):]


def test_bundle_payload_top_level_schema_is_frozen() -> None:
    decision_ref = _run_success()
    payload = get_copilot_artifact_bundle_v1(_artifact_id_from_ref(decision_ref))

    assert list(payload.keys()) == [
        "advisory_decision",
        "explainability",
        "report_markdown",
        "scenario_table_markdown",
        "ladder_table_markdown",
    ]
    assert isinstance(payload["advisory_decision"], dict)
    assert isinstance(payload["explainability"], dict)
    assert isinstance(payload["report_markdown"], str)
    assert payload["scenario_table_markdown"] is None or isinstance(payload["scenario_table_markdown"], str)
    assert payload["ladder_table_markdown"] is None or isinstance(payload["ladder_table_markdown"], str)


def test_bundle_payload_roundtrip_is_deterministic_for_same_inputs() -> None:
    ref1 = _run_success()
    ref2 = _run_success()

    payload1 = get_copilot_artifact_bundle_v1(_artifact_id_from_ref(ref1))
    payload2 = get_copilot_artifact_bundle_v1(_artifact_id_from_ref(ref2))

    assert payload1 == payload2
    s1 = json.dumps(payload1, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    s2 = json.dumps(payload2, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert s1 == s2
