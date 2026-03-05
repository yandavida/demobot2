from __future__ import annotations

import datetime
from decimal import Decimal
from pathlib import Path
import re

import pytest

from core.pricing.fx.types import FxMarketSnapshot
from core.risk.scenario_spec import ScenarioSpec
from core.services.advisory_read_model_v1 import run_treasury_advisory_v1
from core.services.rolling_hedge_ladder_v1 import RollingHedgeLadderConfigV1
from core.services.rolling_hedge_ladder_v1 import compute_rolling_hedge_ladder_v1


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _base_snapshot() -> FxMarketSnapshot:
    return FxMarketSnapshot(
        as_of_ts=datetime.datetime(
            2026,
            3,
            4,
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
        spot_shocks=(Decimal("-0.05"), Decimal("0.0"), Decimal("0.05")),
        df_domestic_shocks=(Decimal("0.0"),),
        df_foreign_shocks=(Decimal("0.0"),),
    )


def test_a_forbidden_import_and_scope_leakage_scan() -> None:
    modules = [
        "core/services/advisory_read_model_v1.py",
        "core/services/rolling_hedge_ladder_v1.py",
        "core/services/hedge_recommendation_v1.py",
        "core/services/hedge_policy_constraints_v1.py",
    ]

    forbidden_runtime_patterns = [
        r"\bimport\s+random\b",
        r"\bfrom\s+random\s+import\b",
        r"\bdatetime\.now\(",
        r"\bdatetime\.utcnow\(",
        r"\btime\.time\(",
        r"\bdate\.today\(",
        r"\butcnow\(",
    ]
    forbidden_provider_fallback = [
        r"provider\s*fallback",
        r"fallback\s*provider",
    ]

    allowed_advisory_pricing_imports = {
        "from core.pricing.fx.types import FXForwardContract",
        "from core.pricing.fx.types import FxMarketSnapshot",
        "from core.pricing.fx.valuation_context import ValuationContext",
    }

    for module in modules:
        text = _read(module)

        for pattern in forbidden_runtime_patterns:
            assert re.search(pattern, text) is None, f"forbidden runtime usage in {module}: {pattern}"

        for pattern in forbidden_provider_fallback:
            assert re.search(pattern, text, flags=re.IGNORECASE) is None, f"forbidden provider fallback usage in {module}: {pattern}"

        pricing_lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip().startswith("from core.pricing") or line.strip().startswith("import core.pricing")
        ]

        if module == "core/services/advisory_read_model_v1.py":
            for line in pricing_lines:
                assert line in allowed_advisory_pricing_imports, (
                    f"unexpected direct pricing import in {module}: {line}"
                )
        else:
            assert not pricing_lines, f"direct core.pricing imports are forbidden in {module}: {pricing_lines}"


def test_b_pr9_6_sync_guard_delta_tolerance_class() -> None:
    text = _read("tests/services/test_advisory_read_model_v1.py")

    assert "MetricClass.DELTA" in text
    assert "DEFAULT_TOLERANCES[MetricClass.DELTA]" in text


def test_c_determinism_smoke_advisory_e2e() -> None:
    payload = {
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

    out1 = run_treasury_advisory_v1(
        payload,
        base_snapshot=_base_snapshot(),
        scenario_spec=_scenario_spec(),
        target_worst_loss_domestic=200000.0,
    )
    out2 = run_treasury_advisory_v1(
        payload,
        base_snapshot=_base_snapshot(),
        scenario_spec=_scenario_spec(),
        target_worst_loss_domestic=200000.0,
    )

    assert out1.to_dict() == out2.to_dict()
    assert out1.delta_exposure_aggregate_domestic is not None
    assert out1.notes == ()


def test_d_determinism_smoke_rolling_ladder_and_as_of_date_required() -> None:
    payload = {
        "contract_version": "v1",
        "company_id": "treasury-demo",
        "snapshot_id": "snap-usdils-20260304",
        "scenario_template_id": "usdils_spot_pm5",
        "exposures": [
            {
                "currency_pair": "USD/ILS",
                "direction": "receivable",
                "notional": "1000000",
                "maturity_date": "2026-03-24",
                "hedge_ratio": "0.60",
            },
            {
                "currency_pair": "USD/ILS",
                "direction": "receivable",
                "notional": "1500000",
                "maturity_date": "2026-04-23",
                "hedge_ratio": "0.50",
            },
            {
                "currency_pair": "USD/ILS",
                "direction": "receivable",
                "notional": "2000000",
                "maturity_date": "2026-05-23",
                "hedge_ratio": "0.40",
            },
        ],
    }

    config = RollingHedgeLadderConfigV1(
        buckets_days=(30, 60, 90),
        roll_frequency_days=30,
        target_worst_loss_total_domestic=200000.0,
        as_of_date="2026-03-04",
    )

    ladder1 = compute_rolling_hedge_ladder_v1(
        payload,
        base_snapshot=_base_snapshot(),
        scenario_spec=_scenario_spec(),
        config=config,
    )
    ladder2 = compute_rolling_hedge_ladder_v1(
        payload,
        base_snapshot=_base_snapshot(),
        scenario_spec=_scenario_spec(),
        config=config,
    )

    assert ladder1.to_dict() == ladder2.to_dict()

    with pytest.raises(ValueError):
        RollingHedgeLadderConfigV1(
            buckets_days=(30, 60, 90),
            roll_frequency_days=30,
            target_worst_loss_total_domestic=200000.0,
            as_of_date="",
        )
