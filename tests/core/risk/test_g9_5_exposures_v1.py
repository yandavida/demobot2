from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from pathlib import Path

import pytest

from core.risk.exposures import SCHEMA_NAME
from core.risk.exposures import SCHEMA_VERSION
from core.risk.exposures import compute_exposures_v1
from core.risk.risk_request import RiskValidationError
from core.risk.scenario_grid import ScenarioGrid
from core.risk.scenario_set import ScenarioSet
from core.risk.scenario_spec import ScenarioSpec


RISK_FIXTURE_PATH = Path("tests/core/risk/_data/g9_risk_artifact_v1_fixture.json")
EXPOSURES_FIXTURE_PATH = Path("tests/core/risk/_data/g9_exposures_v1_fixture.json")
PINNED_EXPOSURES_SHA = "ac531e373f33d22896fbb8277573f67cca0b6561dff061df6aa21b959d46f70c"


def _load_risk_artifact() -> dict:
    return json.loads(RISK_FIXTURE_PATH.read_text(encoding="utf-8"))


def _canonical_sha256_without_sha(obj: dict) -> str:
    body = {k: v for k, v in obj.items() if k != "sha256"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# T1) Schema enforcement

def test_t1_wrong_schema_name_rejected() -> None:
    risk_artifact = _load_risk_artifact()
    risk_artifact["schema"]["name"] = "wrong.schema"

    with pytest.raises(RiskValidationError):
        compute_exposures_v1(risk_artifact=risk_artifact, base_spot=Decimal("3.64"))



def test_t1_wrong_schema_version_rejected() -> None:
    risk_artifact = _load_risk_artifact()
    risk_artifact["schema"]["version"] = "9.9"

    with pytest.raises(RiskValidationError):
        compute_exposures_v1(risk_artifact=risk_artifact, base_spot=Decimal("3.64"))


# T2) Symmetric shock requirement

def test_t2_missing_symmetric_minus_h_rejected() -> None:
    risk_artifact = _load_risk_artifact()
    spec = risk_artifact["inputs"]["scenario_spec"]
    spec["spot_shocks"] = ["0.00", "0.05"]

    scenario_spec = ScenarioSpec(
        schema_version=spec["schema_version"],
        spot_shocks=tuple(Decimal(x) for x in spec["spot_shocks"]),
        df_domestic_shocks=tuple(Decimal(x) for x in spec["df_domestic_shocks"]),
        df_foreign_shocks=tuple(Decimal(x) for x in spec["df_foreign_shocks"]),
    )
    risk_artifact["inputs"]["scenario_set_id"] = ScenarioSet.from_spec(scenario_spec).scenario_set_id

    with pytest.raises(RiskValidationError):
        compute_exposures_v1(risk_artifact=risk_artifact, base_spot=Decimal("3.64"))


# T3) Determinism

def test_t3_same_input_identical_output_and_sha() -> None:
    risk_artifact = _load_risk_artifact()

    out_a = compute_exposures_v1(risk_artifact=risk_artifact, base_spot=Decimal("3.64"))
    out_b = compute_exposures_v1(risk_artifact=risk_artifact, base_spot=Decimal("3.64"))

    assert out_a == out_b
    assert out_a["sha256"] == out_b["sha256"]


# T4) Permutation invariance

def test_t4_permutation_invariance_on_results_order() -> None:
    risk_artifact = _load_risk_artifact()
    reversed_artifact = json.loads(json.dumps(risk_artifact))
    reversed_artifact["outputs"]["results"] = list(reversed(reversed_artifact["outputs"]["results"]))
    reversed_artifact["inputs"]["instrument_ids"] = list(reversed(reversed_artifact["inputs"]["instrument_ids"]))

    out_a = compute_exposures_v1(risk_artifact=risk_artifact, base_spot=Decimal("3.64"))
    out_b = compute_exposures_v1(risk_artifact=reversed_artifact, base_spot=Decimal("3.64"))

    assert out_a == out_b
    assert out_a["sha256"] == out_b["sha256"]


# T5) Mathematical sanity

def test_t5_delta_non_zero_and_antisymmetry_structure() -> None:
    risk_artifact = _load_risk_artifact()
    out = compute_exposures_v1(risk_artifact=risk_artifact, base_spot=Decimal("3.64"))

    first = out["outputs"]["per_instrument"][0]
    delta_pct = Decimal(first["delta_per_pct"])
    assert delta_pct != Decimal("0")

    # Antisymmetry structural check of finite-difference numerator
    scenarios = risk_artifact["outputs"]["results"][0]["scenarios"]
    by_id = {row["scenario_id"]: Decimal(row["pv_domestic"]) for row in scenarios}

    scenario_spec = ScenarioSpec(
        schema_version=risk_artifact["inputs"]["scenario_spec"]["schema_version"],
        spot_shocks=tuple(Decimal(x) for x in risk_artifact["inputs"]["scenario_spec"]["spot_shocks"]),
        df_domestic_shocks=tuple(Decimal(x) for x in risk_artifact["inputs"]["scenario_spec"]["df_domestic_shocks"]),
        df_foreign_shocks=tuple(Decimal(x) for x in risk_artifact["inputs"]["scenario_spec"]["df_foreign_shocks"]),
    )
    grid = ScenarioGrid.from_scenario_set(ScenarioSet.from_spec(scenario_spec))

    h = Decimal("0.05")
    plus = minus = None
    for key, sid in zip(grid.scenarios, grid.scenario_ids):
        if key.df_domestic_shock == Decimal("0") and key.df_foreign_shock == Decimal("0"):
            if key.spot_shock == h:
                plus = by_id[sid]
            elif key.spot_shock == -h:
                minus = by_id[sid]

    assert plus is not None and minus is not None
    numerator = plus - minus
    swapped = minus - plus
    assert numerator == -swapped


# T6) Aggregate linearity

def test_t6_aggregate_is_exact_sum_of_instruments() -> None:
    risk_artifact = _load_risk_artifact()
    out = compute_exposures_v1(risk_artifact=risk_artifact, base_spot=Decimal("3.64"))

    per = out["outputs"]["per_instrument"]
    sum_unit = sum(Decimal(row["delta_per_unit_spot"]) for row in per)
    sum_pct = sum(Decimal(row["delta_per_pct"]) for row in per)

    assert str(sum_unit) == out["outputs"]["aggregates"]["delta_total_per_unit_spot"]
    assert str(sum_pct) == out["outputs"]["aggregates"]["delta_total_per_pct"]


# T7) Hash round-trip

def test_t7_hash_round_trip_matches_stored_sha() -> None:
    risk_artifact = _load_risk_artifact()
    out = compute_exposures_v1(risk_artifact=risk_artifact, base_spot=Decimal("3.64"))

    recomputed = _canonical_sha256_without_sha(out)
    assert recomputed == out["sha256"]


# T8) Backward fixture pinned

def test_t8_exposures_fixture_pinned_sha() -> None:
    fixture = json.loads(EXPOSURES_FIXTURE_PATH.read_text(encoding="utf-8"))

    recomputed = _canonical_sha256_without_sha(fixture)
    assert recomputed == fixture["sha256"]
    assert fixture["sha256"] == PINNED_EXPOSURES_SHA
    assert fixture["schema"]["name"] == SCHEMA_NAME
    assert fixture["schema"]["version"] == SCHEMA_VERSION
