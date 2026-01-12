Title: ADR-010 — Golden Regression Governance (Immutable-by-Version)

Status
------
ACCEPTED

Context
-------
Applies to: Gate R — Regression Harness

Gate R establishes rules for golden datasets, expected outputs, and their governance. These rules ensure deterministic, auditable regression testing.

Decision
--------
Golden datasets and expected outputs SHALL be versioned and immutable-by-version. Any change to inputs or expected outputs SHALL require a new version, accompanied by an updated manifest entry, a new expected hash, and an explicit PR explanation documenting the change.

Rationale
---------
- Versioned immutability ensures historical reproducibility and traceability of regressions.\
- Requiring a manifest update and hash prevents accidental edits and supports automated detection of drift.\
- Centralized comparison policy (policy tolerances only) keeps assertions consistent across datasets.

Consequences
------------
- All dataset artifacts MUST be recorded in `tests/golden/datasets_manifest.json` with `input_file` and `input_sha256`.\
- Expected outputs MUST be hashed and recorded in `tests/golden/expected_hashes.json`.\
- Any change to an existing dataset requires a version bump and a PR that updates manifest and hash entries.\
- Comparison logic shall rely solely on `core/numeric_policy.DEFAULT_TOLERANCES` (no local thresholds).

Evidence / References
---------------------
- Manifest: `tests/golden/datasets_manifest.json`\
- Expected hashes: `tests/golden/expected_hashes.json`\
- Harness: `tests/golden/test_golden_regression.py` and `tests/golden/test_datasets_manifest.py`\
- Gate R doc: `docs/architecture/gate-r-regression-harness-v2.md`
