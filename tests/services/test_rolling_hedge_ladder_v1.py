from __future__ import annotations

import datetime
import math
from decimal import Decimal

from core.numeric_policy import DEFAULT_TOLERANCES
from core.numeric_policy import MetricClass
from core.pricing.fx.types import FxMarketSnapshot
from core.risk.scenario_spec import ScenarioSpec
from core.services.hedge_policy_constraints_v1 import HedgePolicyV1
from core.services.rolling_hedge_ladder_v1 import RollingHedgeLadderConfigV1
from core.services.rolling_hedge_ladder_v1 import compute_rolling_hedge_ladder_v1


def _close(a: float, b: float) -> bool:
    tol = DEFAULT_TOLERANCES[MetricClass.PNL]
    return math.isclose(a, b, rel_tol=float(tol.rel or 0.0), abs_tol=float(tol.abs or 0.0))


def test_rolling_hedge_ladder_end_to_end_deterministic() -> None:
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

    base_snapshot = FxMarketSnapshot(
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
    scenario_spec = ScenarioSpec(
        schema_version=1,
        spot_shocks=(Decimal("-0.05"), Decimal("0.0"), Decimal("0.05")),
        df_domestic_shocks=(Decimal("0.0"),),
        df_foreign_shocks=(Decimal("0.0"),),
    )
    config = RollingHedgeLadderConfigV1(
        buckets_days=(30, 60, 90),
        roll_frequency_days=30,
        target_worst_loss_total_domestic=200000.0,
        as_of_date="2026-03-04",
        policy=HedgePolicyV1(
            policy_id="treasury-policy-1",
            min_hedge_ratio=0.5,
            max_hedge_ratio=0.9,
            rounding_lot_notional=50000.0,
            allow_overhedge=False,
        ),
    )

    out_a = compute_rolling_hedge_ladder_v1(
        payload,
        base_snapshot=base_snapshot,
        scenario_spec=scenario_spec,
        config=config,
    )
    out_b = compute_rolling_hedge_ladder_v1(
        payload,
        base_snapshot=base_snapshot,
        scenario_spec=scenario_spec,
        config=config,
    )

    assert out_a.to_dict() == out_b.to_dict()

    assert [row.exposures_count for row in out_a.buckets] == [1, 1, 1]
    assert [row.bucket_label for row in out_a.buckets] == ["0-30", "31-60", "61-90"]

    allocated_total = sum(row.hedge_recommendation.target_worst_loss_domestic for row in out_a.buckets)
    assert _close(allocated_total, config.target_worst_loss_total_domestic)

    for row in out_a.buckets:
        assert row.risk_summary.contract_version == "v1"
        assert row.hedge_recommendation.contract_version == "v1"
        assert row.policy_result is not None
