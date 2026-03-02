from __future__ import annotations

from decimal import Decimal

import pytest

from core.risk.risk_request import RiskValidationError
from core.risk.scenario_grid import ScenarioGrid
from core.risk.scenario_grid import ScenarioKey
from core.risk.scenario_grid import SUPPORTED_SCHEMA_VERSION
from core.risk.scenario_set import ScenarioSet
from core.risk.scenario_spec import ScenarioSpec


def _spec(*, spot: tuple[Decimal, ...], dfd: tuple[Decimal, ...], dff: tuple[Decimal, ...], version: int = 1) -> ScenarioSpec:
    return ScenarioSpec(
        schema_version=version,
        spot_shocks=spot,
        df_domestic_shocks=dfd,
        df_foreign_shocks=dff,
    )


def _scenario_set(spec: ScenarioSpec) -> ScenarioSet:
    return ScenarioSet.from_spec(spec)


# T1: schema_version required

def test_t1_schema_version_required() -> None:
    spec = _spec(
        spot=(Decimal("-0.05"), Decimal("0.00"), Decimal("0.05")),
        dfd=(Decimal("-0.01"), Decimal("0.00")),
        dff=(Decimal("-0.02"), Decimal("0.00")),
    )
    with pytest.raises(RiskValidationError) as exc_info:
        ScenarioGrid.from_scenario_set(_scenario_set(spec), schema_version=None)  # type: ignore[arg-type]
    assert exc_info.value.envelope.code == "MISSING_SCHEMA_VERSION"


# T2: unsupported schema_version rejected

def test_t2_unsupported_schema_version_rejected() -> None:
    spec = _spec(
        spot=(Decimal("-0.05"), Decimal("0.00"), Decimal("0.05")),
        dfd=(Decimal("-0.01"), Decimal("0.00")),
        dff=(Decimal("-0.02"), Decimal("0.00")),
    )
    with pytest.raises(RiskValidationError) as exc_info:
        ScenarioGrid.from_scenario_set(_scenario_set(spec), schema_version=99)
    assert exc_info.value.envelope.code == "UNSUPPORTED_SCHEMA_VERSION"


# T3: scenario count equals Cartesian size

def test_t3_cartesian_count() -> None:
    spec = _spec(
        spot=(Decimal("-0.05"), Decimal("0.00"), Decimal("0.05")),
        dfd=(Decimal("-0.01"), Decimal("0.00"), Decimal("0.01")),
        dff=(Decimal("-0.02"), Decimal("0.00")),
    )
    grid = ScenarioGrid.from_scenario_set(_scenario_set(spec))
    assert len(grid.scenarios) == 3 * 3 * 2
    assert len(grid.scenario_ids) == len(grid.scenarios)


# T4: deterministic ordering proof

def test_t4_rebuild_is_identical_order_and_ids() -> None:
    spec = _spec(
        spot=(Decimal("-0.05"), Decimal("0.00"), Decimal("0.05")),
        dfd=(Decimal("-0.01"), Decimal("0.00"), Decimal("0.01")),
        dff=(Decimal("-0.02"), Decimal("0.00")),
    )
    scenario_set = _scenario_set(spec)
    grid_a = ScenarioGrid.from_scenario_set(scenario_set)
    grid_b = ScenarioGrid.from_scenario_set(scenario_set)

    assert grid_a.scenarios == grid_b.scenarios
    assert grid_a.scenario_ids == grid_b.scenario_ids


# T5: invariance to construction order

def test_t5_spec_insertion_order_invariance() -> None:
    spec_a = _spec(
        spot=(Decimal("-0.05"), Decimal("0.00"), Decimal("0.05")),
        dfd=(Decimal("-0.01"), Decimal("0.00"), Decimal("0.01")),
        dff=(Decimal("-0.02"), Decimal("0.00"), Decimal("0.02")),
    )
    spec_b = _spec(
        spot=(Decimal("0.05"), Decimal("-0.05"), Decimal("0.00")),
        dfd=(Decimal("0.01"), Decimal("-0.01"), Decimal("0.00")),
        dff=(Decimal("0.02"), Decimal("-0.02"), Decimal("0.00")),
    )

    set_a = _scenario_set(spec_a)
    set_b = _scenario_set(spec_b)

    assert set_a.scenario_set_id == set_b.scenario_set_id

    grid_a = ScenarioGrid.from_scenario_set(set_a)
    grid_b = ScenarioGrid.from_scenario_set(set_b)

    assert grid_a.scenarios == grid_b.scenarios
    assert grid_a.scenario_ids == grid_b.scenario_ids


# T6: uniqueness

def test_t6_scenario_ids_unique() -> None:
    spec = _spec(
        spot=(Decimal("-0.05"), Decimal("0.00"), Decimal("0.05")),
        dfd=(Decimal("-0.01"), Decimal("0.00"), Decimal("0.01")),
        dff=(Decimal("-0.02"), Decimal("0.00"), Decimal("0.02")),
    )
    grid = ScenarioGrid.from_scenario_set(_scenario_set(spec))
    assert len(set(grid.scenario_ids)) == len(grid.scenario_ids)


# T7: explicit lexicographic ordering

def test_t7_first_and_last_match_lexicographic_min_max() -> None:
    spec = _spec(
        spot=(Decimal("-0.05"), Decimal("0.00"), Decimal("0.05")),
        dfd=(Decimal("-0.01"), Decimal("0.00"), Decimal("0.01")),
        dff=(Decimal("-0.02"), Decimal("0.00"), Decimal("0.02")),
    )
    grid = ScenarioGrid.from_scenario_set(_scenario_set(spec))

    assert grid.scenarios[0] == ScenarioKey(
        spot_shock=Decimal("-0.05"),
        df_domestic_shock=Decimal("-0.01"),
        df_foreign_shock=Decimal("-0.02"),
    )
    assert grid.scenarios[-1] == ScenarioKey(
        spot_shock=Decimal("0.05"),
        df_domestic_shock=Decimal("0.01"),
        df_foreign_shock=Decimal("0.02"),
    )


# T8: canonical id sensitivity

def test_t8_change_one_shock_changes_ids() -> None:
    base_spec = _spec(
        spot=(Decimal("-0.05"), Decimal("0.00"), Decimal("0.05")),
        dfd=(Decimal("-0.01"), Decimal("0.00"), Decimal("0.01")),
        dff=(Decimal("-0.02"), Decimal("0.00"), Decimal("0.02")),
    )
    changed_spec = _spec(
        spot=(Decimal("-0.05"), Decimal("0.00"), Decimal("0.06")),
        dfd=(Decimal("-0.01"), Decimal("0.00"), Decimal("0.01")),
        dff=(Decimal("-0.02"), Decimal("0.00"), Decimal("0.02")),
    )

    base_grid = ScenarioGrid.from_scenario_set(_scenario_set(base_spec))
    changed_grid = ScenarioGrid.from_scenario_set(_scenario_set(changed_spec))

    assert base_grid.scenario_set_id != changed_grid.scenario_set_id
    assert base_grid.scenario_ids != changed_grid.scenario_ids
    assert set(base_grid.scenario_ids) != set(changed_grid.scenario_ids)


def test_grid_is_frozen_immutable() -> None:
    spec = _spec(
        spot=(Decimal("0.00"),),
        dfd=(Decimal("0.00"),),
        dff=(Decimal("0.00"),),
    )
    grid = ScenarioGrid.from_scenario_set(_scenario_set(spec))
    with pytest.raises((AttributeError, TypeError)):
        grid.schema_version = SUPPORTED_SCHEMA_VERSION + 1  # type: ignore[misc]
