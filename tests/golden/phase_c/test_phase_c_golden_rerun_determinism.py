from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.golden.phase_c.test_phase_c_golden_regression import _artifact_payload


pytestmark = pytest.mark.golden


def test_phase_c_replay_is_deterministic() -> None:
    manifest = json.loads(Path("tests/golden/phase_c/datasets_manifest.json").read_text(encoding="utf-8"))
    assert manifest, "phase_c datasets_manifest must not be empty"

    for entry in manifest:
        dataset_id = entry["dataset_id"]
        version = entry["version"]
        input_payload = json.loads(Path(entry["input_file"]).read_text(encoding="utf-8"))

        first = _artifact_payload(dataset_id, version, input_payload["resolved_inputs"])
        second = _artifact_payload(dataset_id, version, input_payload["resolved_inputs"])

        assert first == second
        assert first["canonical_payload_hash"] == second["canonical_payload_hash"]