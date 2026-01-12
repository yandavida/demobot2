import json
import hashlib
from pathlib import Path
import math
import importlib


np = importlib.import_module("core.numeric_policy")
bs = importlib.import_module("core.pricing.bs")
units = importlib.import_module("core.pricing.units")


def sha256_hex(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        h.update(f.read())
    return h.hexdigest()


def load_expected(path: Path):
    return json.loads(path.read_text())


def assert_close_metric(metric_name, metric_class, actual, expected):
    tol = np.DEFAULT_TOLERANCES.get(metric_class)
    assert tol is not None, f"No tolerance for {metric_class}"
    abs_tol = tol.abs or 0.0
    rel_tol = tol.rel or 0.0
    if not math.isclose(actual, expected, abs_tol=abs_tol, rel_tol=rel_tol):
        abs_diff = abs(actual - expected)
        rel_diff = abs_diff / (abs(expected) if expected != 0 else 1.0)
        raise AssertionError(
            f"Metric {metric_name}: expected={expected}, actual={actual}, abs_diff={abs_diff}, rel_diff={rel_diff}, tol=(abs={abs_tol}, rel={rel_tol})"
        )


def test_expected_hashes_and_files_exist():
    hashes = json.loads(Path("tests/golden/expected_hashes.json").read_text())
    for p, h in hashes.items():
        pp = Path(p)
        assert pp.exists(), f"Expected file missing: {p}"
        actual = sha256_hex(pp)
        assert actual == h, f"Hash mismatch for {p}: expected {h}, got {actual}"


def test_golden_expected_matches_computed():
    # Manifest-driven harness: iterate all datasets declared in the manifest
    manifest_path = Path("tests/golden/datasets_manifest.json")
    assert manifest_path.exists(), "Missing manifest: tests/golden/datasets_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    entries = manifest.get("datasets", [])
    assert entries, "Manifest contains no datasets"

    for entry in entries:
        dataset_id = entry.get("dataset_id")
        version = entry.get("version")
        input_file = entry.get("input_file")
        assert dataset_id and version and input_file, f"Manifest entry missing keys: {entry}"

        expected_path = Path(f"tests/golden/expected/{dataset_id}/expected_v{version}.json")
        assert expected_path.exists(), f"Expected file missing for dataset {dataset_id}: {expected_path}"
        expected = load_expected(expected_path)

        inputs_path = Path(input_file)
        assert inputs_path.exists(), f"Input file for dataset {dataset_id} not found: {inputs_path}"
        inputs = json.loads(inputs_path.read_text())

        # For each case, compute price + greeks, canonicalize, and compare
        for exp_case, inp in zip(expected.get("cases", []), inputs):
            case_id = exp_case.get("id")
            # compute
            opt = inp["option_type"]
            spot = float(inp["spot"])
            strike = float(inp["strike"])
            t = float(inp["t"])
            rate = float(inp["rate"])
            div = float(inp["div"])
            vol = float(inp["vol"])

            price = bs.bs_price('call' if opt == 'C' else 'put', spot, strike, rate, div, vol, t)
            raw = bs.bs_greeks(opt, spot, strike, rate, div, vol, t)
            canon = units.to_canonical_greeks(raw)

            metrics_expected = exp_case["metrics"]
            mapping = [
                ("price", np.MetricClass.PRICE),
                ("delta", np.MetricClass.DELTA),
                ("gamma", np.MetricClass.GAMMA),
                ("vega", np.MetricClass.VEGA),
                ("theta", np.MetricClass.THETA),
                ("rho", np.MetricClass.RHO),
            ]

            for name, mclass in mapping:
                expected_value = metrics_expected.get(name)
                if expected_value is None:
                    continue
                actual_value = price if name == "price" else canon.get(name)
                try:
                    assert_close_metric(name, mclass, float(actual_value), float(expected_value))
                except AssertionError as e:
                    raise AssertionError(f"Dataset {dataset_id} case {case_id} - " + str(e))
