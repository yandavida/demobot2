import json
import hashlib
from pathlib import Path


MANIFEST_PATH = Path("tests/golden/pipeline/datasets_manifest.json")


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def test_pipeline_manifest_well_formed_and_integrity():
    assert MANIFEST_PATH.exists(), f"manifest not found: {MANIFEST_PATH}"
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, list), "manifest root must be a JSON array"

    required_keys = {
        "dataset_id": str,
        "version": int,
        "description": str,
        "input_file": str,
        "input_sha256": str,
        "generator": str,
        "notes": str,
    }

    for entry in data:
        assert isinstance(entry, dict), "each manifest entry must be an object"
        for k, t in required_keys.items():
            assert k in entry, f"missing key '{k}' in manifest entry"
            assert isinstance(entry[k], t), f"key '{k}' must be of type {t.__name__}"

        input_path = Path(entry["input_file"])
        assert input_path.exists(), f"input file referenced in manifest does not exist: {input_path}"

        actual = compute_sha256(input_path)
        expected = entry["input_sha256"]
        assert actual == expected, (
            f"sha256 mismatch for {input_path}: expected {expected}, got {actual}"
        )
