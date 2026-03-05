from __future__ import annotations

import datetime
import math
from decimal import Decimal

from core.numeric_policy import DEFAULT_TOLERANCES
from core.numeric_policy import MetricClass
from core.pricing.fx.types import FxMarketSnapshot
from core.risk.scenario_spec import ScenarioSpec
from core.services.advisory_read_model_v1 import run_treasury_advisory_v1


def test_end_to_end_treasury_advisory_is_deterministic() -> None:
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

    out_a = run_treasury_advisory_v1(
        payload,
        base_snapshot=base_snapshot,
        scenario_spec=scenario_spec,
        target_worst_loss_domestic=200000.0,
    )
    out_b = run_treasury_advisory_v1(
        payload,
        base_snapshot=base_snapshot,
        scenario_spec=scenario_spec,
        target_worst_loss_domestic=200000.0,
    )

    tol = DEFAULT_TOLERANCES[MetricClass.DELTA]
    rel_tol = float(tol.rel or 0.0)
    abs_tol = float(tol.abs or 0.0)

    assert out_a.to_dict() == out_b.to_dict()
    assert len(out_a.risk_summary.scenario_rows) == 3
    assert out_a.risk_summary.worst_loss_domestic < 0
    assert 300000.0 < abs(out_a.risk_summary.worst_loss_domestic) < 400000.0
    assert math.isclose(out_a.hedge_recommendation.recommended_hedge_ratio, 0.7587954212, rel_tol=1e-6, abs_tol=1e-6)
    assert out_a.delta_exposure_aggregate_domestic is not None
    assert out_a.delta_exposure_aggregate_domestic > 0
    assert math.isclose(out_a.delta_exposure_aggregate_domestic, 6633360.0, rel_tol=rel_tol, abs_tol=abs_tol)
    assert out_a.notes == ()
