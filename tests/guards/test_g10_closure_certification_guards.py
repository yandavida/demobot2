from __future__ import annotations

import ast
import hashlib
from pathlib import Path

from core.risk import exposures
from core.risk import portfolio_surface
from core.risk import risk_artifact
from tests.core.risk.test_g10_4_options_harness_flow import _build_artifacts


ROOT = Path(__file__).resolve().parents[2]
RISK_DATA_DIR = ROOT / "tests" / "core" / "risk" / "_data"

G10_FIXTURES = {
    RISK_DATA_DIR / "g10_options_risk_artifact_v1_fixture.json": "617f07527bcbee0ae1f3fea3c7fb5e3fe719771ae5021504ec0b24bd2074b41b",
    RISK_DATA_DIR / "g10_options_exposures_v1_fixture.json": "60f906ef595d703e23203fb02fe1fd63c56f6b1cd5668d881ffb56a1cb80df02",
    RISK_DATA_DIR / "g10_options_portfolio_surface_v1_fixture.json": "920d1b94b815e2019452360aaebb8aa9e626b5c9525dd2f63125d171ca154a96",
}

G9_FIXTURES = {
    RISK_DATA_DIR / "g9_risk_artifact_v1_fixture.json": "fd7f108c82fd0f3835564ad5777eee101b5f9c514769c151809f01f773f5097d",
    RISK_DATA_DIR / "g9_exposures_v1_fixture.json": "9eafb0f9c25297556bc307d52cfd736bc9760528d2a0d76cda33c3f8c3a16f8d",
    RISK_DATA_DIR / "g9_portfolio_surface_v1_fixture.json": "99cfbf2e9528f2489b0e34ec5bf59eb4c47628eb9169f4efd9b6e61269a96bce",
}

G10_MODULES = (
    ROOT / "core" / "contracts" / "option_contract_v1.py",
    ROOT / "core" / "pricing" / "bs_ssot_v1.py",
    ROOT / "core" / "market_data" / "market_snapshot_payload_v0.py",
    ROOT / "core" / "market_data" / "df_lookup_v0.py",
    ROOT / "core" / "risk" / "reprice_harness.py",
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _iter_import_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.append(node.module)
    return modules


def test_t1_g10_fixture_hashes_are_pinned() -> None:
    for fixture_path, expected_sha in G10_FIXTURES.items():
        assert fixture_path.exists(), f"missing fixture: {fixture_path}"
        assert _sha256_file(fixture_path) == expected_sha


def test_t2_g9_artifact_contracts_and_fixtures_unchanged() -> None:
    assert risk_artifact.SCHEMA_NAME == "pe.g9.risk_artifact"
    assert risk_artifact.SCHEMA_VERSION == "1.0"

    assert exposures.SCHEMA_NAME == "pe.g9.exposures_artifact"
    assert exposures.SCHEMA_VERSION == "1.0"

    assert portfolio_surface.SCHEMA_NAME == "pe.g9.portfolio_surface_artifact"
    assert portfolio_surface.SCHEMA_VERSION == "1.0"

    for fixture_path, expected_sha in G9_FIXTURES.items():
        assert fixture_path.exists(), f"missing fixture: {fixture_path}"
        assert _sha256_file(fixture_path) == expected_sha


def test_t3_g10_modules_forbidden_import_and_token_guard() -> None:
    forbidden_import_roots = {
        "random",
        "numpy.random",
        "scipy",
        "quantlib",
        "QuantLib",
        "stochastic",
    }

    for module_path in G10_MODULES:
        assert module_path.exists(), f"missing module: {module_path}"

        imports = _iter_import_modules(module_path)
        for mod in imports:
            lower_mod = mod.lower()
            for token in forbidden_import_roots:
                assert not lower_mod.startswith(token.lower()), f"forbidden import '{mod}' in {module_path}"

        text = module_path.read_text(encoding="utf-8")
        assert "datetime.now(" not in text, f"forbidden token datetime.now found in {module_path}"


def test_t4_determinism_smoke_for_g10_options_flow() -> None:
    risk_a, exposures_a, surface_a = _build_artifacts()
    risk_b, exposures_b, surface_b = _build_artifacts()

    for artifact in (risk_a, exposures_a, surface_a):
        assert "schema" in artifact
        assert "engine" in artifact
        assert "inputs" in artifact
        assert "outputs" in artifact
        assert "hashing" in artifact
        assert "sha256" in artifact

    assert risk_a == risk_b
    assert exposures_a == exposures_b
    assert surface_a == surface_b
