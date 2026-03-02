from __future__ import annotations

import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from core.pricing.fx import types as fx_types
from core.pricing.fx.valuation_context import ValuationContext
from core.risk.reprice_harness import reprice_fx_forward_risk
from core.risk.risk_request import RiskRequest
from core.risk.risk_request import RiskValidationError
from core.risk.scenario_grid import ScenarioGrid
from core.risk.scenario_set import ScenarioSet
from core.risk.scenario_spec import ScenarioSpec


def _context() -> ValuationContext:
    return ValuationContext(
        as_of_ts=datetime.datetime(2026, 3, 2, 12, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=2))),
        domestic_currency="ILS",
        strict_mode=True,
    )


def _base_snapshot() -> fx_types.FxMarketSnapshot:
    return fx_types.FxMarketSnapshot(
        as_of_ts=_context().as_of_ts,
        spot_rate=3.64,
        df_domestic=0.995,
        df_foreign=0.9982,
    )


def _contract(*, forward_rate: float = 3.65, direction: str = "receive_foreign_pay_domestic") -> fx_types.FXForwardContract:
    return fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="ILS",
        notional=1_000_000.0,
        forward_date=datetime.date(2026, 4, 2),
        forward_rate=forward_rate,
        direction=direction,
    )


def _spec(*, spot: tuple[Decimal, ...], dfd: tuple[Decimal, ...], dff: tuple[Decimal, ...]) -> ScenarioSpec:
    return ScenarioSpec(
        schema_version=1,
        spot_shocks=spot,
        df_domestic_shocks=dfd,
        df_foreign_shocks=dff,
    )


def _request(*, instrument_ids: tuple[str, ...], spec: ScenarioSpec) -> RiskRequest:
    return RiskRequest(
        schema_version=1,
        valuation_context=_context(),
        market_snapshot_id="snap-g9-3-001",
        instrument_ids=instrument_ids,
        scenario_spec=spec,
        strict=True,
    )


def _grid(spec: ScenarioSpec) -> ScenarioGrid:
    return ScenarioGrid.from_scenario_set(ScenarioSet.from_spec(spec))


def _contracts() -> dict[str, fx_types.FXForwardContract]:
    return {
        "fwd_a": _contract(forward_rate=3.65),
        "fwd_b": _contract(forward_rate=3.60),
    }


# T1: Base repricing determinism

def test_t1_same_inputs_identical_risk_result() -> None:
    spec = _spec(
        spot=(Decimal("-0.05"), Decimal("0.00"), Decimal("0.05")),
        dfd=(Decimal("0.00"),),
        dff=(Decimal("0.00"),),
    )
    request = _request(instrument_ids=("fwd_a", "fwd_b"), spec=spec)
    grid = _grid(spec)

    result_a = reprice_fx_forward_risk(request, _base_snapshot(), grid, _contracts())
    result_b = reprice_fx_forward_risk(request, _base_snapshot(), grid, _contracts())

    assert result_a == result_b


# T2: Scenario count alignment

def test_t2_per_instrument_scenario_count_matches_grid() -> None:
    spec = _spec(
        spot=(Decimal("-0.05"), Decimal("0.00"), Decimal("0.05")),
        dfd=(Decimal("-0.01"), Decimal("0.00"), Decimal("0.01")),
        dff=(Decimal("0.00"),),
    )
    request = _request(instrument_ids=("fwd_a", "fwd_b"), spec=spec)
    grid = _grid(spec)

    result = reprice_fx_forward_risk(request, _base_snapshot(), grid, _contracts())
    for cube in result.results:
        assert len(cube.scenario_pvs) == len(grid.scenarios)


# T3: Ordering invariance

def test_t3_results_and_scenarios_keep_canonical_ordering() -> None:
    spec = _spec(
        spot=(Decimal("-0.05"), Decimal("0.00"), Decimal("0.05")),
        dfd=(Decimal("-0.01"), Decimal("0.00"), Decimal("0.01")),
        dff=(Decimal("-0.02"), Decimal("0.00"), Decimal("0.02")),
    )
    request = _request(instrument_ids=("fwd_b", "fwd_a"), spec=spec)
    grid = _grid(spec)

    result = reprice_fx_forward_risk(request, _base_snapshot(), grid, _contracts())

    assert tuple(cube.instrument_id for cube in result.results) == ("fwd_a", "fwd_b")
    first_grid_id = grid.scenario_ids[0]
    last_grid_id = grid.scenario_ids[-1]
    assert result.results[0].scenario_pvs[0].scenario_id == first_grid_id
    assert result.results[0].scenario_pvs[-1].scenario_id == last_grid_id


# T4: Permutation invariance (instrument input order)

def test_t4_instrument_input_permutation_same_output() -> None:
    spec = _spec(
        spot=(Decimal("-0.05"), Decimal("0.00"), Decimal("0.05")),
        dfd=(Decimal("0.00"),),
        dff=(Decimal("0.00"),),
    )
    request_a = _request(instrument_ids=("fwd_b", "fwd_a"), spec=spec)
    request_b = _request(instrument_ids=("fwd_a", "fwd_b"), spec=spec)
    grid = _grid(spec)

    result_a = reprice_fx_forward_risk(request_a, _base_snapshot(), grid, _contracts())
    result_b = reprice_fx_forward_risk(request_b, _base_snapshot(), grid, _contracts())

    assert result_a == result_b


# T5: Shock sensitivity sanity

def test_t5_non_zero_spot_shock_changes_pv() -> None:
    spec = _spec(
        spot=(Decimal("0.00"), Decimal("0.05")),
        dfd=(Decimal("0.00"),),
        dff=(Decimal("0.00"),),
    )
    request = _request(instrument_ids=("fwd_a",), spec=spec)
    grid = _grid(spec)

    result = reprice_fx_forward_risk(request, _base_snapshot(), grid, {"fwd_a": _contract(forward_rate=3.65)})
    cube = result.results[0]

    base_pv = cube.base_pv
    shocked_pv = None
    for key, pv_item in zip(grid.scenarios, cube.scenario_pvs):
        if key.spot_shock == Decimal("0.05"):
            shocked_pv = pv_item.pv_domestic
            break

    assert shocked_pv is not None
    assert shocked_pv != base_pv


# T6: Reject invalid shocks ((1+shock) <= 0)

def test_t6_reject_factor_non_positive() -> None:
    spec = _spec(
        spot=(Decimal("-1.00"),),
        dfd=(Decimal("0.00"),),
        dff=(Decimal("0.00"),),
    )
    request = _request(instrument_ids=("fwd_a",), spec=spec)
    grid = _grid(spec)

    with pytest.raises(RiskValidationError):
        reprice_fx_forward_risk(request, _base_snapshot(), grid, {"fwd_a": _contract()})


# T7: DF positivity maintained

def test_t7_reject_non_positive_shocked_df() -> None:
    spec = _spec(
        spot=(Decimal("0.00"),),
        dfd=(Decimal("0.00"),),
        dff=(Decimal("0.00"),),
    )
    request = _request(instrument_ids=("fwd_a",), spec=spec)
    grid = _grid(spec)

    bad_snapshot = _base_snapshot()
    object.__setattr__(bad_snapshot, "df_domestic", 0.0)

    with pytest.raises(RiskValidationError):
        reprice_fx_forward_risk(request, bad_snapshot, grid, {"fwd_a": _contract()})


# T8: No forbidden imports (light)

def test_t8_harness_has_no_lifecycle_or_api_imports() -> None:
    harness_path = Path("core/risk/reprice_harness.py")
    text = harness_path.read_text(encoding="utf-8")

    forbidden = (
        "import random",
        "from random",
        "import time",
        "from time",
        "import pandas",
        "from pandas",
        "import api",
        "from api",
        "lifecycle",
    )
    for token in forbidden:
        assert token not in text, f"Forbidden import/token in reprice_harness.py: {token}"
