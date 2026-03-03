from __future__ import annotations

import ast
import hashlib
import json
from decimal import Decimal
from pathlib import Path

from core.risk import exposures
from core.risk import portfolio_surface
from core.risk import risk_artifact
from core.risk.exposures import compute_exposures_v1
from core.risk.portfolio_surface import compute_portfolio_surface_v1
from core.risk.scenario_grid import ScenarioGrid
from core.risk.scenario_set import ScenarioSet
from core.risk.scenario_spec import ScenarioSpec


ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = ROOT / "tests" / "core" / "risk" / "_data"

RISK_FIXTURE = FIXTURES_DIR / "g9_risk_artifact_v1_fixture.json"
EXPOSURES_FIXTURE = FIXTURES_DIR / "g9_exposures_v1_fixture.json"
PORTFOLIO_FIXTURE = FIXTURES_DIR / "g9_portfolio_surface_v1_fixture.json"

PINNED_FIXTURE_SHA256 = {
    RISK_FIXTURE.name: "fd7f108c82fd0f3835564ad5777eee101b5f9c514769c151809f01f773f5097d",
    EXPOSURES_FIXTURE.name: "9eafb0f9c25297556bc307d52cfd736bc9760528d2a0d76cda33c3f8c3a16f8d",
    PORTFOLIO_FIXTURE.name: "99cfbf2e9528f2489b0e34ec5bf59eb4c47628eb9169f4efd9b6e61269a96bce",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_scenario_spec_from_risk_artifact(risk_fixture: dict) -> ScenarioSpec:
    raw = risk_fixture["inputs"]["scenario_spec"]
    return ScenarioSpec(
        schema_version=int(raw["schema_version"]),
        spot_shocks=tuple(Decimal(v) for v in raw["spot_shocks"]),
        df_domestic_shocks=tuple(Decimal(v) for v in raw["df_domestic_shocks"]),
        df_foreign_shocks=tuple(Decimal(v) for v in raw["df_foreign_shocks"]),
    )


def _find_pm_h_scenario_ids(risk_fixture: dict) -> tuple[Decimal, str, str]:
    spec = _parse_scenario_spec_from_risk_artifact(risk_fixture)
    positive_h = sorted({h for h in spec.spot_shocks if h > 0 and (-h) in spec.spot_shocks})
    assert len(positive_h) == 1
    h = positive_h[0]

    scenario_set = ScenarioSet.from_spec(spec)
    grid = ScenarioGrid.from_scenario_set(scenario_set)

    plus_id = None
    minus_id = None
    for key, scenario_id in zip(grid.scenarios, grid.scenario_ids):
        if key.df_domestic_shock == Decimal("0") and key.df_foreign_shock == Decimal("0"):
            if key.spot_shock == h:
                plus_id = scenario_id
            elif key.spot_shock == -h:
                minus_id = scenario_id

    assert plus_id is not None
    assert minus_id is not None
    return h, plus_id, minus_id


def _iter_imports_from_python_file(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def _is_forbidden_import(module_name: str) -> bool:
    if module_name.startswith("numpy.random"):
        return True

    parts = module_name.split(".")
    forbidden_parts = {
        "random",
        "time",
        "pandas",
        "requests",
        "lifecycle",
        "api",
        "service_sqlite",
        "bot",
    }
    return any(part in forbidden_parts for part in parts)


def test_t1_artifact_schemas_frozen() -> None:
    assert risk_artifact.SCHEMA_NAME == "pe.g9.risk_artifact"
    assert risk_artifact.SCHEMA_VERSION == "1.0"

    assert exposures.SCHEMA_NAME == "pe.g9.exposures_artifact"
    assert exposures.SCHEMA_VERSION == "1.0"

    assert portfolio_surface.SCHEMA_NAME == "pe.g9.portfolio_surface_artifact"
    assert portfolio_surface.SCHEMA_VERSION == "1.0"


def test_t2_no_forbidden_imports_in_core_risk_modules() -> None:
    risk_dir = ROOT / "core" / "risk"
    violations: list[str] = []

    for path in sorted(risk_dir.rglob("*.py")):
        for module_name in _iter_imports_from_python_file(path):
            if _is_forbidden_import(module_name):
                rel = path.relative_to(ROOT).as_posix()
                violations.append(f"{rel}: {module_name}")

    assert not violations, "Forbidden imports found in core/risk modules:\n" + "\n".join(violations)


def test_t3_artifact_fixture_hashes_unchanged() -> None:
    for fixture_path in (RISK_FIXTURE, EXPOSURES_FIXTURE, PORTFOLIO_FIXTURE):
        assert _sha256_file(fixture_path) == PINNED_FIXTURE_SHA256[fixture_path.name]


def test_t4_end_to_end_consistency_smoke() -> None:
    risk_fixture = _load_json(RISK_FIXTURE)
    portfolio_fixture = _load_json(PORTFOLIO_FIXTURE)

    exposures_artifact = compute_exposures_v1(risk_fixture, base_spot=Decimal("1"))
    portfolio_artifact = compute_portfolio_surface_v1(risk_fixture)

    per_instrument_sum = sum(
        (Decimal(row["delta_per_pct"]) for row in exposures_artifact["outputs"]["per_instrument"]),
        start=Decimal("0"),
    )
    delta_total_per_pct = Decimal(exposures_artifact["outputs"]["aggregates"]["delta_total_per_pct"])
    assert delta_total_per_pct == per_instrument_sum

    h, plus_id, minus_id = _find_pm_h_scenario_ids(risk_fixture)
    scenario_totals = {
        row["scenario_id"]: Decimal(row["pv_domestic"])
        for row in risk_fixture["outputs"]["aggregates"]["scenario_total_pv_domestic"]
    }
    expected_total_delta_per_pct = (scenario_totals[plus_id] - scenario_totals[minus_id]) / (Decimal("2") * h)
    assert delta_total_per_pct == expected_total_delta_per_pct

    expected_ranking_order = [
        row["scenario_id"]
        for row in portfolio_fixture["outputs"]["ranking_worst_to_best"]
    ]
    actual_ranking_order = [
        row["scenario_id"]
        for row in portfolio_artifact["outputs"]["ranking_worst_to_best"]
    ]
    assert actual_ranking_order == expected_ranking_order