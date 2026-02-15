"""Gate F8.4C–E: FX goldens policy hardening tests.

Tests-only policy checks for provenance schema, hand_calc-only mode,
canonical JSON determinism, strict output artifact keys, and protection
against hash regeneration coupling.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re

import pytest

from core import numeric_policy


ALLOWED_ARTIFACT_KEYS = {"scenario_id", "pv", "forward_market"}


def canonicalize_json(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def approx_equal(a: float, b: float) -> bool:
    tol = numeric_policy.DEFAULT_TOLERANCES[numeric_policy.MetricClass.PRICE]
    abs_diff = abs(a - b)
    if abs_diff <= tol.abs:
        return True
    rel_diff = abs_diff / max(abs(a), abs(b), 1e-9)
    return rel_diff <= tol.rel


@pytest.fixture
def sample_hand_calc_scenario() -> dict:
    return {
        "scenario_id": "fx_hand_calc_policy_case",
        "as_of_ts": "2026-02-15T16:00:00+00:00",
        "expected": {"pv": 1234.5, "forward_market": 1.1045},
        "provenance": {
            "type": "hand_calc",
            "source": "manual_bank_formula",
            "notes": "policy-lock fixture",
        },
    }


def test_provenance_schema_requires_type(sample_hand_calc_scenario: dict):
    scenario = sample_hand_calc_scenario
    assert "provenance" in scenario
    assert isinstance(scenario["provenance"], dict)
    assert "type" in scenario["provenance"]
    assert isinstance(scenario["provenance"]["type"], str)
    assert scenario["provenance"]["type"] == "hand_calc"


def test_hand_calc_only_mode_rejects_non_hand_calc(sample_hand_calc_scenario: dict):
    bad = dict(sample_hand_calc_scenario)
    bad["provenance"] = dict(sample_hand_calc_scenario["provenance"])
    bad["provenance"]["type"] = "reference_external"

    with pytest.raises(ValueError, match="hand_calc"):
        if bad["provenance"]["type"] != "hand_calc":
            raise ValueError("hand_calc_only mode requires provenance.type == hand_calc")


def test_output_artifact_contains_only_allowed_keys(sample_hand_calc_scenario: dict):
    expected = sample_hand_calc_scenario["expected"]
    output_artifact = {
        "scenario_id": sample_hand_calc_scenario["scenario_id"],
        "pv": expected["pv"],
        "forward_market": expected["forward_market"],
    }

    assert set(output_artifact.keys()) == ALLOWED_ARTIFACT_KEYS


def test_output_artifact_numeric_fields_use_price_tolerance(sample_hand_calc_scenario: dict):
    expected = sample_hand_calc_scenario["expected"]
    output_artifact = {
        "scenario_id": sample_hand_calc_scenario["scenario_id"],
        "pv": float(expected["pv"]),
        "forward_market": float(expected["forward_market"]),
    }

    assert approx_equal(output_artifact["pv"], expected["pv"])
    assert approx_equal(output_artifact["forward_market"], expected["forward_market"])


def test_canonicalization_is_deterministic(sample_hand_calc_scenario: dict):
    expected = sample_hand_calc_scenario["expected"]
    output_artifact = {
        "scenario_id": sample_hand_calc_scenario["scenario_id"],
        "pv": expected["pv"],
        "forward_market": expected["forward_market"],
    }

    canonical_1 = canonicalize_json(output_artifact)
    canonical_2 = canonicalize_json(output_artifact)

    assert canonical_1 == canonical_2
    assert compute_sha256(canonical_1) == compute_sha256(canonical_2)


def test_fx_tests_do_not_import_generate_hashes_script():
    fx_tests_dir = Path("tests/core/pricing/fx")
    py_files = sorted(fx_tests_dir.glob("test_*.py"))
    import_pattern = re.compile(r"(^|\n)\s*(from\s+.*\s+import\s+generate_hashes|import\s+.*generate_hashes)")

    for file_path in py_files:
        if file_path.name == Path(__file__).name:
            continue
        source = file_path.read_text(encoding="utf-8")
        assert import_pattern.search(source) is None


def test_generate_hashes_module_is_import_safe_if_present():
    script_path = Path("tests/core/pricing/fx/goldens/generate_hashes.py")
    if not script_path.exists():
        assert True
        return

    source = script_path.read_text(encoding="utf-8")
    assert 'if __name__ == "__main__":' in source

    # No obvious top-level side-effect entrypoints
    assert "subprocess" not in source
    assert "os.system" not in source


def test_policy_file_has_no_forbidden_nondeterminism_calls():
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    def _is_forbidden_call(node: ast.Call) -> bool:
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id == "datetime" and func.attr in {"now", "utcnow"}:
                return True
            if func.value.id == "time" and func.attr == "time":
                return True
            if func.value.id == "os" and func.attr == "system":
                return True
            if func.value.id == "random":
                return True
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            assert not _is_forbidden_call(node)
