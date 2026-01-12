import json
import hashlib
from pathlib import Path
import pytest

pytestmark = pytest.mark.golden


def sha256_hex(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        h.update(f.read())
    return h.hexdigest()


def test_manifest_and_inputs_exist_and_hash_match():
    manifest_path = Path("tests/golden/datasets_manifest.json")
    assert manifest_path.exists(), "Missing manifest: tests/golden/datasets_manifest.json"

    data = json.loads(manifest_path.read_text())
    assert "datasets" in data and isinstance(data["datasets"], list), "Manifest must contain 'datasets' list"

    for entry in data["datasets"]:
        # required keys
        for k in ("dataset_id", "version", "description", "domain", "input_file", "input_sha256"):
            assert k in entry, f"Manifest entry missing '{k}' for dataset {entry.get('dataset_id')!r}"

        dataset_id = entry["dataset_id"]
        input_file = Path(entry["input_file"])
        assert input_file.exists(), f"Input file for dataset {dataset_id!r} not found: {input_file}"

        actual_sha = sha256_hex(input_file)
        expected_sha = entry["input_sha256"]
        assert actual_sha == expected_sha, (
            f"SHA mismatch for dataset {dataset_id!r}: expected {expected_sha}, got {actual_sha}"
        )
