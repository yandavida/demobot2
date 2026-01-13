from __future__ import annotations

import numpy as np
import pandas as pd

from core.models import Leg, Position
from core.backtest_engine import BacktestConfig, run_full_backtest


FORBIDDEN_DYNAMIC_FIELDS = {
    "timestamp",
    "ts",
    "id",
    "uuid",
    "sid",
    "eid",
    "created_at",
    "applied_at",
}


def _assert_no_dynamic_fields(records: list[dict]):
    for r in records:
        for k in r.keys():
            assert k not in FORBIDDEN_DYNAMIC_FIELDS, f"Dynamic field present: {k}"


def test_backtest_surfaces_ordering_and_no_dynamic_fields():
    # Simple two-leg position
    legs = [Leg(side="long", cp="CALL", strike=100.0, quantity=1, premium=1.0),
            Leg(side="short", cp="PUT", strike=95.0, quantity=1, premium=0.5)]
    position = Position(legs=legs)

    cfg = BacktestConfig(
        position=position,
        spot=100.0,
        lower_factor=0.9,
        upper_factor=1.1,
        num_points=21,
        dte_days=30,
        iv=0.2,
        r=0.01,
        q=0.0,
        contract_multiplier=100,
    )

    res = run_full_backtest(position, cfg)

    curve_df: pd.DataFrame = res["curve_df"]
    scenarios_df: pd.DataFrame = res["scenarios_df"]

    # Curve prices must be strictly ascending (stable ordering)
    prices = np.asarray(curve_df["price"].to_list(), dtype=float)
    assert np.all(np.diff(prices) > 0), "Curve prices are not strictly increasing"

    # Scenarios must follow the canonical moves order (in percent)
    expected_moves = [-10.0, -5.0, -2.0, 0.0, 2.0, 5.0, 10.0]
    moves = [float(x) for x in scenarios_df["Move %"].to_list()]
    assert moves == expected_moves, f"Scenarios Move % ordering changed: {moves}"

    # Ensure no dynamic fields in exported records
    curve_records = curve_df.to_dict(orient="records")
    scenarios_records = scenarios_df.to_dict(orient="records")
    _assert_no_dynamic_fields(curve_records)
    _assert_no_dynamic_fields(scenarios_records)


# Note: we intentionally avoid calling higher-level SaaS service/router here
# to keep the test hermetic and focused on contract surface outputs.
