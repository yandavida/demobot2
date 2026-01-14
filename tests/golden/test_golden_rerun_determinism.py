from __future__ import annotations

import json
from pathlib import Path
import importlib

import pytest


def _canonical_json(obj: object) -> str:
    # Match the repository's golden serializer used when writing expected files:
    # json.dumps(..., indent=2) with insertion order preserved.
    return json.dumps(obj, indent=2)


def _generate_expected_for_dataset(dataset_id: str, version: int) -> dict:
    # Reuse the same generator logic as the harness: compute price+greeks
    manifest = json.loads(Path("tests/golden/datasets_manifest.json").read_text())
    entry = next((e for e in manifest.get("datasets", []) if e.get("dataset_id") == dataset_id and e.get("version") == version), None)
    if entry is None:
        import pytest

        pytest.skip(f"Dataset {dataset_id} v{version} not found in manifest; skipping determinism guard")
    inputs_path = Path(entry["input_file"])
    inputs = json.loads(inputs_path.read_text())

    bs = importlib.import_module("core.pricing.bs")
    units = importlib.import_module("core.pricing.units")

    # Build expected payload with the same header fields and ordering
    expected = {}
    expected["dataset_id"] = dataset_id
    expected["version"] = version
    expected["policy_ref"] = "core.numeric_policy.DEFAULT_TOLERANCES"
    expected["units"] = {"vega": "per_1pct_iv", "theta": "per_calendar_day"}
    expected["cases"] = []
    for inp in inputs:
        opt = inp.get("option_type")
        spot = float(inp.get("spot"))
        strike = float(inp.get("strike"))
        t = float(inp.get("t"))
        rate = float(inp.get("rate"))
        div = float(inp.get("div"))
        vol = float(inp.get("vol"))

        price = bs.bs_price("call" if opt == "C" else "put", spot, strike, rate, div, vol, t)
        # bs_greeks canonical call using cp keyword
        raw = bs.bs_greeks(cp=opt, spot=spot, strike=strike, t=t, rate=rate, div=div, vol=vol)
        canon = units.to_canonical_greeks(raw)
        metrics = {"price": float(price)}
        for k in ("delta", "gamma", "vega", "theta", "rho"):
            if k in canon:
                metrics[k] = float(canon[k])

        expected["cases"].append({"id": inp.get("id"), "metrics": metrics})

    return expected


@pytest.mark.golden
def test_bs_canonical_golden_rerun_deterministic():
    # Generate twice and compare canonicalized JSON; then compare to checked-in expected
    dataset_id = "bs_canonical"
    version = 1

    gen1 = _generate_expected_for_dataset(dataset_id, version)
    gen2 = _generate_expected_for_dataset(dataset_id, version)
    s1 = _canonical_json(gen1)
    s2 = _canonical_json(gen2)
    assert s1 == s2, "Repeated generation produced different outputs"

    # Compare byte-for-byte with committed expected file using the same
    # serializer (indent=2) and insertion ordering.
    expected_path = Path(f"tests/golden/expected/{dataset_id}/expected_v{version}.json")
    assert expected_path.exists(), f"Committed expected file missing: {expected_path}"
    committed_text = expected_path.read_text()
    # produced_text should match the committed file exactly
    assert s1 == committed_text, "Generated expected differs from committed golden expected (byte mismatch)"
