from __future__ import annotations

import os
import subprocess
import sys

from core.market_data.artifact_store import put_market_snapshot
from core.market_data.market_snapshot_payload_v0 import Curve
from core.market_data.market_snapshot_payload_v0 import FxRates
from core.market_data.market_snapshot_payload_v0 import InterestRateCurves
from core.market_data.market_snapshot_payload_v0 import MarketConventions
from core.market_data.market_snapshot_payload_v0 import MarketSnapshotPayloadV0
from core.market_data.market_snapshot_payload_v0 import SpotPrices
from core.portfolio.advisory_payload_artifact_store_v1 import put_advisory_payload_artifact_v1


def _env() -> dict[str, str]:
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    paths = ["src", "."]
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


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


def test_cli_missing_run_args_returns_exit_2() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "scripts.treasury_copilot_cli_v1", "--question", "תעשה גידור"],
        capture_output=True,
        text=True,
        env=_env(),
        check=False,
    )

    assert result.returncode == 2
    assert "missing_required_args=" in result.stdout


def test_cli_invalid_decision_ref_returns_exit_3() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.treasury_copilot_cli_v1",
            "--question",
            "למה המלצת על זה",
            "--as-of-decision-ref",
            "artifact_bundle:missing",
        ],
        capture_output=True,
        text=True,
        env=_env(),
        check=False,
    )

    assert result.returncode == 3
    assert "followup_resolution_failed_v1" in result.stdout


def test_cli_run_success_outputs_warning_and_decision_ref() -> None:
    market_snapshot_id = put_market_snapshot(_market_payload())
    portfolio_artifact_id = put_advisory_payload_artifact_v1(_payload(market_snapshot_id))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.treasury_copilot_cli_v1",
            "--question",
            "תעשה גידור",
            "--market-snapshot-id",
            market_snapshot_id,
            "--scenario-template-id",
            "STANDARD_7",
            "--policy-template-id",
            "TREASURY_STANDARD_70",
            "--portfolio-ref",
            f"artifact:{portfolio_artifact_id}",
        ],
        capture_output=True,
        text=True,
        env=_env(),
        check=False,
    )

    assert result.returncode == 0
    assert "fx_advisory_executed_v1" in result.stdout
    assert "decision_ref=artifact_bundle:" in result.stdout
    assert result.stdout.strip() != ""
