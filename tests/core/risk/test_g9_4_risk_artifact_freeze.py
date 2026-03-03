from __future__ import annotations

import datetime
import hashlib
import json
from decimal import Decimal
from pathlib import Path

from core.pricing.fx import types as fx_types
from core.pricing.fx.valuation_context import ValuationContext
from core.risk.reprice_harness import reprice_fx_forward_risk
from core.risk.risk_artifact import ENGINE_NAME
from core.risk.risk_artifact import ENGINE_VERSION
from core.risk.risk_artifact import SCHEMA_NAME
from core.risk.risk_artifact import SCHEMA_VERSION
from core.risk.risk_artifact import build_risk_artifact_v1
from core.risk.risk_request import RiskRequest
from core.risk.scenario_grid import ScenarioGrid
from core.risk.scenario_set import ScenarioSet
from core.risk.scenario_spec import ScenarioSpec


FIXTURE_PATH = Path(__file__).resolve().parent / "_data" / "g9_risk_artifact_v1_fixture.json"
PINNED_FIXTURE_SHA256 = "9168d05f6cddaed091bed9ab45ef20ba0a5c148ba3a17de211e857f67dd5e4a6"


def _canonical_sha256_without_field(obj: dict, field: str = "sha256") -> str:
    payload = {k: v for k, v in obj.items() if k != field}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _context() -> ValuationContext:
    return ValuationContext(
        as_of_ts=datetime.datetime(2026, 3, 2, 12, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=2))),
        domestic_currency="ILS",
        strict_mode=True,
    )


def _snapshot() -> fx_types.FxMarketSnapshot:
    return fx_types.FxMarketSnapshot(
        as_of_ts=_context().as_of_ts,
        spot_rate=3.64,
        df_domestic=0.995,
        df_foreign=0.9982,
    )


def _contract(*, strike: float) -> fx_types.FXForwardContract:
    return fx_types.FXForwardContract(
        base_currency="USD",
        quote_currency="ILS",
        notional=1_000_000.0,
        forward_date=datetime.date(2026, 4, 2),
        forward_rate=strike,
        direction="receive_foreign_pay_domestic",
    )


def _spec() -> ScenarioSpec:
    return ScenarioSpec(
        schema_version=1,
        spot_shocks=(Decimal("-0.05"), Decimal("0.00"), Decimal("0.05")),
        df_domestic_shocks=(Decimal("-0.01"), Decimal("0.00"), Decimal("0.01")),
        df_foreign_shocks=(Decimal("-0.02"), Decimal("0.00"), Decimal("0.02")),
    )


def _request(*, instrument_ids: tuple[str, ...]) -> RiskRequest:
    return RiskRequest(
        schema_version=1,
        valuation_context=_context(),
        market_snapshot_id="snap-g9-4-001",
        instrument_ids=instrument_ids,
        scenario_spec=_spec(),
        strict=True,
    )


def _grid() -> ScenarioGrid:
    return ScenarioGrid.from_scenario_set(ScenarioSet.from_spec(_spec()))


def _contracts() -> dict[str, fx_types.FXForwardContract]:
    return {
        "fwd_a": _contract(strike=3.65),
        "fwd_b": _contract(strike=3.60),
    }


def _artifact(*, instrument_ids: tuple[str, ...]) -> dict:
    request = _request(instrument_ids=instrument_ids)
    grid = _grid()
    result = reprice_fx_forward_risk(request, _snapshot(), grid, _contracts())
    return build_risk_artifact_v1(request, grid, result)


# T1) Schema/version freeze

def test_t1_schema_and_engine_identity_freeze() -> None:
    artifact = _artifact(instrument_ids=("fwd_b", "fwd_a"))

    assert artifact["schema"]["name"] == SCHEMA_NAME
    assert artifact["schema"]["version"] == SCHEMA_VERSION
    assert artifact["engine"]["name"] == ENGINE_NAME
    assert artifact["engine"]["version"] == ENGINE_VERSION


# T2) Required keys freeze

def test_t2_required_keys_freeze() -> None:
    artifact = _artifact(instrument_ids=("fwd_b", "fwd_a"))

    assert set(artifact.keys()) == {"schema", "engine", "inputs", "outputs", "hashing", "sha256"}

    assert "market_snapshot_id" in artifact["inputs"]
    assert "scenario_set_id" in artifact["inputs"]
    assert "instrument_ids" in artifact["inputs"]

    assert "results" in artifact["outputs"]
    assert "aggregates" in artifact["outputs"]
    assert "base_total_pv_domestic" in artifact["outputs"]["aggregates"]
    assert "scenario_total_pv_domestic" in artifact["outputs"]["aggregates"]

    first_result = artifact["outputs"]["results"][0]
    assert "instrument_id" in first_result
    assert "base" in first_result
    assert "scenarios" in first_result

    first_scenario = first_result["scenarios"][0]
    assert "scenario_id" in first_scenario
    assert "pv_domestic" in first_scenario


# T3) Hash round-trip immutability

def test_t3_hash_round_trip_immutability() -> None:
    artifact = _artifact(instrument_ids=("fwd_a", "fwd_b"))
    recomputed = _canonical_sha256_without_field(artifact, "sha256")
    assert recomputed == artifact["sha256"]


# T4) Backward-compat fixture

def test_t4_fixture_hash_and_required_keys() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    recomputed = _canonical_sha256_without_field(fixture, "sha256")
    assert recomputed == fixture["sha256"]
    assert fixture["sha256"] == PINNED_FIXTURE_SHA256

    assert set(fixture.keys()) == {"schema", "engine", "inputs", "outputs", "hashing", "sha256"}
    assert "market_snapshot_id" in fixture["inputs"]
    assert "scenario_set_id" in fixture["inputs"]
    assert "instrument_ids" in fixture["inputs"]
    assert "base_total_pv_domestic" in fixture["outputs"]["aggregates"]


# T5) Determinism

def test_t5_identical_inputs_identical_artifact_and_sha() -> None:
    artifact_a = _artifact(instrument_ids=("fwd_a", "fwd_b"))
    artifact_b = _artifact(instrument_ids=("fwd_a", "fwd_b"))

    assert artifact_a == artifact_b
    assert artifact_a["sha256"] == artifact_b["sha256"]


# T6) Permutation invariance (instrument input order)

def test_t6_permutation_invariance_on_input_order() -> None:
    artifact_a = _artifact(instrument_ids=("fwd_b", "fwd_a"))
    artifact_b = _artifact(instrument_ids=("fwd_a", "fwd_b"))

    assert artifact_a == artifact_b
    assert artifact_a["sha256"] == artifact_b["sha256"]
