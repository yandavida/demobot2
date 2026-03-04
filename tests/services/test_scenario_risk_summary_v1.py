from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

import pytest

from core.services.scenario_risk_summary_v1 import summarize_scenario_risk_v1


DATA_DIR = Path("tests/core/risk/_data")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _fixtures() -> tuple[dict, dict]:
    risk = _load_json(DATA_DIR / "g10_options_risk_artifact_v1_fixture.json")
    surface = _load_json(DATA_DIR / "g10_options_portfolio_surface_v1_fixture.json")
    return risk, surface


def _canon(summary) -> str:
    return json.dumps(asdict(summary), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def test_deterministic_output_twice_identical_serialization() -> None:
    risk, surface = _fixtures()
    out_a = summarize_scenario_risk_v1(risk, surface)
    out_b = summarize_scenario_risk_v1(risk, surface)

    assert _canon(out_a) == _canon(out_b)


def test_worst_scenario_matches_portfolio_surface_top_rank() -> None:
    risk, surface = _fixtures()
    summary = summarize_scenario_risk_v1(risk, surface)

    top_rank = min(surface["outputs"]["ranking_worst_to_best"], key=lambda row: (int(row["rank"]), row["scenario_id"]))
    assert summary.worst_scenario_id == top_rank["scenario_id"]
    assert summary.worst_total_pv_domestic == float(top_rank["total_pv_domestic"])


def test_scenario_rows_ordering_is_stable_and_deterministic() -> None:
    risk, surface = _fixtures()
    summary = summarize_scenario_risk_v1(risk, surface)

    key_tuples = [(row.pnl_vs_base_domestic, row.scenario_id) for row in summary.scenario_rows]
    assert key_tuples == sorted(key_tuples, key=lambda t: (t[0], t[1]))


def test_pnl_vs_base_computed_from_artifact_values() -> None:
    risk, surface = _fixtures()
    summary = summarize_scenario_risk_v1(risk, surface)

    base = summary.base_total_pv_domestic
    for row in summary.scenario_rows:
        assert row.pnl_vs_base_domestic == pytest.approx(row.total_pv_domestic - base)


def test_no_hidden_recomputation_with_minimal_artifacts() -> None:
    risk_min = {
        "inputs": {
            "market_snapshot_id": "snap-min",
        },
        "outputs": {
            "aggregates": {
                "base_total_pv_domestic": "100.0",
                "scenario_total_pv_domestic": [
                    {"scenario_id": "scn_a", "pv_domestic": "80.0"},
                    {"scenario_id": "scn_b", "pv_domestic": "120.0"},
                ],
            }
        },
    }
    surface_min = {
        "inputs": {
            "market_snapshot_id": "snap-min",
        },
        "outputs": {
            "ranking_worst_to_best": [
                {"scenario_id": "scn_a", "rank": 1, "total_pv_domestic": "80.0"},
                {"scenario_id": "scn_b", "rank": 2, "total_pv_domestic": "120.0"},
            ]
        },
    }

    summary = summarize_scenario_risk_v1(risk_min, surface_min)

    assert summary.snapshot_id == "snap-min"
    assert summary.base_total_pv_domestic == 100.0
    assert summary.worst_scenario_id == "scn_a"
    assert summary.worst_total_pv_domestic == 80.0
    assert summary.worst_loss_domestic == -20.0
    assert [r.scenario_id for r in summary.scenario_rows] == ["scn_a", "scn_b"]
    assert [r.label for r in summary.scenario_rows] == ["", ""]
