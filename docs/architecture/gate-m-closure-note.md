# Gate M Closure Note

- Gate M enforces SNAPSHOT compute to be `market_snapshot_id`-anchored (no implicit/live lookup).
- Snapshot identity is content-addressed via `market_snapshot_id = sha256(canonical_json(payload))` (see `core/market_data/identity.py`).
- Artifact storage is immutable and idempotent (`put_market_snapshot` / `get_market_snapshot`) — tested by `tests/market_data/test_artifact_store.py`.
- Validators enforce schema-level requirements: missing/invalid `market_snapshot_id` → 400 (see `tests/api/v2/test_v2_compute_snapshot_id_validation.py`).
- Service boundary enforces replay-only resolution and maps errors: missing artifact → 404, semantic mismatch → 422 (see `api/v2/service_sqlite.py` and `tests/api/v2/test_v2_compute_snapshot_integration.py`).
- Semantic market validations (M3) are unit-tested for missing symbol/FX/curve/tenor cases (`tests/market_data/test_market_requirements_validation.py`).
- Replay evidence (M4) includes permutation-invariance and restart determinism tests (`tests/api/v2/test_v2_m4_replay_evidence.py`).
- No production code changes or schema edits were required to close M4; evidence is tests-only.
