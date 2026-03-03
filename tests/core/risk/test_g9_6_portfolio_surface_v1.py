from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from pathlib import Path

import pytest

from core.risk.portfolio_surface import SCHEMA_NAME
from core.risk.portfolio_surface import SCHEMA_VERSION
from core.risk.portfolio_surface import compute_portfolio_surface_v1
from core.risk.risk_request import RiskValidationError


RISK_FIXTURE_PATH = Path("tests/core/risk/_data/g9_risk_artifact_v1_fixture.json")
SURFACE_FIXTURE_PATH = Path("tests/core/risk/_data/g9_portfolio_surface_v1_fixture.json")
PINNED_SURFACE_SHA = "bde8e0cc8d1e22cb4b0f2ad3a6d73227221d49c268f343ddf0a969c856a6c9e3"


def _load_risk_artifact() -> dict:
    return json.loads(RISK_FIXTURE_PATH.read_text(encoding="utf-8"))


def _canonical_sha256_without_sha(obj: dict) -> str:
    body = {k: v for k, v in obj.items() if k != "sha256"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# T1) Schema enforcement

def test_t1_wrong_schema_name_rejected() -> None:
    artifact = _load_risk_artifact()
    artifact["schema"]["name"] = "wrong.schema"
    with pytest.raises(RiskValidationError):
        compute_portfolio_surface_v1(artifact)


def test_t1_wrong_schema_version_rejected() -> None:
    artifact = _load_risk_artifact()
    artifact["schema"]["version"] = "9.9"
    with pytest.raises(RiskValidationError):
        compute_portfolio_surface_v1(artifact)


# T2) Determinism

def test_t2_deterministic_output_and_sha() -> None:
    artifact = _load_risk_artifact()
    out_a = compute_portfolio_surface_v1(artifact)
    out_b = compute_portfolio_surface_v1(artifact)

    assert out_a == out_b
    assert out_a["sha256"] == out_b["sha256"]


# T3) Ordering preservation

def test_t3_scenarios_order_matches_risk_artifact_aggregate_order() -> None:
    artifact = _load_risk_artifact()
    out = compute_portfolio_surface_v1(artifact)

    input_ids = [row["scenario_id"] for row in artifact["outputs"]["aggregates"]["scenario_total_pv_domestic"]]
    output_ids = [row["scenario_id"] for row in out["outputs"]["scenarios"]]

    assert output_ids == input_ids


# T4) Loss correctness

def test_t4_loss_equals_total_minus_base_exactly() -> None:
    artifact = _load_risk_artifact()
    out = compute_portfolio_surface_v1(artifact)

    base = Decimal(out["outputs"]["base_total_pv_domestic"])
    for row in out["outputs"]["scenarios"]:
        total = Decimal(row["total_pv_domestic"])
        loss = Decimal(row["loss_vs_base_domestic"])
        assert loss == total - base


# T5) Ranking correctness + tie-breaker

def test_t5_ranking_sorted_and_ranked_without_gaps() -> None:
    artifact = _load_risk_artifact()
    out = compute_portfolio_surface_v1(artifact)

    ranking = out["outputs"]["ranking_worst_to_best"]
    expected = sorted(
        ranking,
        key=lambda r: (Decimal(r["loss_vs_base_domestic"]), r["scenario_id"]),
    )

    assert ranking == expected
    assert [row["rank"] for row in ranking] == list(range(1, len(ranking) + 1))


def test_t5_tie_breaker_scenario_id_lexicographic() -> None:
    artifact = _load_risk_artifact()
    scenario_totals = artifact["outputs"]["aggregates"]["scenario_total_pv_domestic"]

    # Force tie: two scenarios with identical PV totals
    scenario_totals[0]["pv_domestic"] = scenario_totals[1]["pv_domestic"]

    out = compute_portfolio_surface_v1(artifact)
    ranking = out["outputs"]["ranking_worst_to_best"]

    losses = [Decimal(r["loss_vs_base_domestic"]) for r in ranking]
    for idx in range(len(losses) - 1):
        if losses[idx] == losses[idx + 1]:
            assert ranking[idx]["scenario_id"] <= ranking[idx + 1]["scenario_id"]


# T6) Permutation invariance (instrument order in input risk_artifact)

def test_t6_instrument_order_permutation_does_not_change_surface_sha() -> None:
    artifact = _load_risk_artifact()
    permuted = json.loads(json.dumps(artifact))
    permuted["inputs"]["instrument_ids"] = list(reversed(permuted["inputs"]["instrument_ids"]))
    permuted["outputs"]["results"] = list(reversed(permuted["outputs"]["results"]))

    out_a = compute_portfolio_surface_v1(artifact)
    out_b = compute_portfolio_surface_v1(permuted)

    assert out_a["sha256"] == out_b["sha256"]
    assert out_a == out_b


# T7) Hash round-trip

def test_t7_hash_round_trip_matches_stored_sha() -> None:
    artifact = _load_risk_artifact()
    out = compute_portfolio_surface_v1(artifact)

    recomputed = _canonical_sha256_without_sha(out)
    assert recomputed == out["sha256"]


# T8) Backward fixture

def test_t8_fixture_pinned_and_valid() -> None:
    fixture = json.loads(SURFACE_FIXTURE_PATH.read_text(encoding="utf-8"))
    recomputed = _canonical_sha256_without_sha(fixture)

    assert recomputed == fixture["sha256"]
    assert fixture["sha256"] == PINNED_SURFACE_SHA
    assert fixture["schema"]["name"] == SCHEMA_NAME
    assert fixture["schema"]["version"] == SCHEMA_VERSION
