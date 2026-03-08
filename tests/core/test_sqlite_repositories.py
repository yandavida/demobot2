from __future__ import annotations

import datetime
from pathlib import Path

from core.contracts.model_registry import ModelCapability
from core.contracts.model_registry import ModelRegistryEntry
from core.contracts.reference_data_set import ReferenceDataSet
from core.contracts.valuation_policy_set import ValuationPolicySet
from core.contracts.valuation_run import ValuationRun
from core.persistence.repositories import ModelRegistryRepository
from core.persistence.repositories import ReferenceDataSetRepository
from core.persistence.repositories import ValuationPolicySetRepository
from core.persistence.repositories import ValuationRunRepository
from core.persistence.sqlite_repositories import SqliteModelRegistryRepository
from core.persistence.sqlite_repositories import SqliteReferenceDataSetRepository
from core.persistence.sqlite_repositories import SqliteValuationPolicySetRepository
from core.persistence.sqlite_repositories import SqliteValuationRunRepository


def _db_path(tmp_path: Path) -> str:
    return str(tmp_path / "a7_sqlite_repositories.db")


def _reference_data_set() -> ReferenceDataSet:
    return ReferenceDataSet(
        calendar_version="cal-v2026-01",
        holiday_calendar_refs=("cal.us.nyfed",),
        day_count_convention_refs=("dcc.ACT_365F",),
        business_day_adjustment_refs=("bda.MOD_FOLLOWING",),
        settlement_convention_refs=("set.fx.spot_t2",),
        fixing_source_refs=("fix.wm_reuters_16",),
        exercise_convention_refs=("ex.european.at_expiry",),
        taxonomy_mapping_refs=("tax.fxopt.g10",),
        reference_data_version_id="rds-2026-03-08-001",
    )


def _valuation_policy_set() -> ValuationPolicySet:
    return ValuationPolicySet(
        valuation_policy_id="vps-2026-03-08-001",
        model_family="black_scholes_crr",
        pricing_engine_policy="engine.policy.v1",
        numeric_policy_id="numeric.policy.v1",
        tolerance_policy_id="tol.policy.v1",
        calibration_recipe_id="cal.recipe.v1",
        approval_status="approved",
        policy_version="v1",
        policy_owner="treasury_risk_committee",
        created_timestamp=datetime.datetime(2026, 3, 8, 12, 0, 0, tzinfo=datetime.timezone.utc),
    )


def _valuation_run() -> ValuationRun:
    return ValuationRun(
        valuation_run_id="vr-2026-03-08-001",
        portfolio_state_id="ps-2026-03-08-001",
        market_snapshot_id="ms-2026-03-08-001",
        reference_data_set_id="rds-2026-03-08-001",
        valuation_policy_set_id="vps-2026-03-08-001",
        valuation_context_id="vc-2026-03-08-001",
        scenario_set_id="scn-2026-03-08-001",
        software_build_hash="build-abc123def",
        run_timestamp=datetime.datetime(2026, 3, 8, 12, 0, 0, tzinfo=datetime.timezone.utc),
        valuation_timestamp=datetime.datetime(2026, 3, 8, 11, 59, 0, tzinfo=datetime.timezone.utc),
        run_purpose="risk_snapshot",
    )


def _model_registry_entry() -> ModelRegistryEntry:
    return ModelRegistryEntry(
        model_id="model.fx.bs.v1",
        semantic_version="1.0.0",
        implementation_version="impl-2026-03-08",
        validation_status="approved",
        owner="treasury_model_risk",
        approval_date=datetime.date(2026, 3, 8),
        benchmark_pack_id="bench.fx.options.v1",
        known_limitations=("european-only",),
        numeric_policy_id="numeric.policy.v1",
        supported_capabilities=(
            ModelCapability(
                instrument_family="fx_option_vanilla",
                exercise_style="european",
                measure="pv",
            ),
        ),
    )


def test_sqlite_repositories_conform_to_repository_protocols(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path)

    reference_repo = SqliteReferenceDataSetRepository(db_path=db_path)
    policy_repo = SqliteValuationPolicySetRepository(db_path=db_path)
    run_repo = SqliteValuationRunRepository(db_path=db_path)
    model_repo = SqliteModelRegistryRepository(db_path=db_path)

    assert isinstance(reference_repo, ReferenceDataSetRepository)
    assert isinstance(policy_repo, ValuationPolicySetRepository)
    assert isinstance(run_repo, ValuationRunRepository)
    assert isinstance(model_repo, ModelRegistryRepository)


def test_sqlite_reference_data_set_round_trip_is_deterministic(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path)
    repo = SqliteReferenceDataSetRepository(db_path=db_path)
    reference_data_set = _reference_data_set()

    repo.save(reference_data_set.reference_data_version_id, reference_data_set)
    repo.save(reference_data_set.reference_data_version_id, reference_data_set)

    loaded = repo.get_by_id(reference_data_set.reference_data_version_id)

    assert loaded == reference_data_set
    assert not hasattr(loaded, "table_name")


def test_sqlite_valuation_policy_set_round_trip_is_deterministic(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path)
    repo = SqliteValuationPolicySetRepository(db_path=db_path)
    policy_set = _valuation_policy_set()

    repo.save(policy_set.valuation_policy_id, policy_set)
    repo.save(policy_set.valuation_policy_id, policy_set)

    loaded = repo.get_by_id(policy_set.valuation_policy_id)

    assert loaded == policy_set
    assert not hasattr(loaded, "row_id")


def test_sqlite_valuation_run_round_trip_is_deterministic(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path)
    repo = SqliteValuationRunRepository(db_path=db_path)
    valuation_run = _valuation_run()

    repo.save(valuation_run)
    repo.save(valuation_run)

    loaded = repo.get_by_id(valuation_run.valuation_run_id)

    assert loaded == valuation_run
    assert not hasattr(loaded, "cursor")


def test_sqlite_model_registry_round_trip_is_deterministic(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path)
    repo = SqliteModelRegistryRepository(db_path=db_path)
    model_entry = _model_registry_entry()

    repo.save(model_entry)
    repo.save(model_entry)

    loaded = repo.get_by_model_id(model_entry.model_id)

    assert loaded == model_entry
    assert not hasattr(loaded, "sqlite_row")


def test_sqlite_repositories_return_none_for_missing_ids(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path)

    assert SqliteReferenceDataSetRepository(db_path=db_path).get_by_id("missing-rds") is None
    assert SqliteValuationPolicySetRepository(db_path=db_path).get_by_id("missing-vps") is None
    assert SqliteValuationRunRepository(db_path=db_path).get_by_id("missing-vr") is None
    assert SqliteModelRegistryRepository(db_path=db_path).get_by_model_id("missing-model") is None
