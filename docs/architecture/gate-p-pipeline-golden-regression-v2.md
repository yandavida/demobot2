# Gate P — Pipeline Golden Regression (V2)

**Status:** OPEN (initial definition)

## Purpose

Gate P provides system-/pipeline-level golden regression coverage for deterministic pipeline outputs (for example: portfolio valuation and orchestration outputs). Gate P does NOT change numeric policy or semantics (Gate N) and does NOT modify Gate R (pricing-level golden regression).

## Preconditions (Locked)

- Gate M closed and immutable (market snapshots / replay-only compute)
- Gate N closed and immutable (numeric policy SSOT)
- Gate R closed and immutable (pricing-level golden governance)
- ADR-011: pipeline regression is out of Gate R by design

## In-Scope (Explicit)

- Deterministic pipeline paths that aggregate multiple instruments
- Portfolio valuation outputs (aggregation + FX conversion) only when deterministic adapters/inputs are used
- Deterministic ordering and serialization rules for pipeline outputs

## Non-Goals (Explicit)

- No live market data or provider fallback in the golden path
- No DB/SQLite-backed services in the golden execution path
- No clocks, timestamps, or time-dependent execution in the golden path
- No performance optimization obligations
- No pricing correctness validation against external benchmarks
- No policy/semantics changes (units, tolerances, rounding) — Gate N remains authoritative
- No backtest timeline coverage unless explicitly opened later as a sub-gate

## Determinism Guarantees (Hard Rules)

- Offline only: golden pipeline runs MUST not depend on live network or external providers
- No use of clocks, environment-dependent configuration, or randomness in the golden execution path
- No IO-dependent services; any required context must be provided via deterministic fixtures/adapters
- Inputs must be fixed, canonical, and content-addressed where applicable

## Canonical Output Rules (Pipeline-Level)

- Expected outputs MUST be canonicalized prior to freezing. Canonicalization SHALL include:
  - stable ordering of collections (e.g., deterministic sorting of per-position items)
  - explicit currency and unit fields for numeric values
  - no raw or untyped blobs in expected outputs
- Pipeline outputs MUST remain compatible with Gate N numeric policy (units/tolerances); Gate P does not redefine tolerances.

## Output Schema (Normative)

The pipeline-level expected output is a JSON document with the following minimal structure (fields are normative; no example numeric values are provided here):

- `dataset_id`: string
- `version`: integer
- `policy_ref`: string (reference to Gate N SSOT, e.g., `core.numeric_policy.DEFAULT_TOLERANCES`)
- `portfolio`: object
  - `base_currency`: string
  - `total_pv`: number
  - `per_position`: array of objects (MUST be deterministically ordered)
    - each item:
      - `instrument_id` / `symbol`: string
      - `pv`: number
      - `currency`: string
      - `greeks`: optional object (only present if pipeline produces canonical greeks)
        - `delta`, `gamma`, `vega`, `theta`, `rho` — numbers (units per Gate N)
- `units`: object (explicit unit labels used in the document, e.g., vega unit label)
- `metadata`: object (free-form metadata: provenance, dataset description)

Notes:

- The `per_position` array MUST be sorted deterministically (e.g., by `instrument_id`) before freezing expected outputs.\
- `greeks` are optional in the schema only if the pipeline path provides canonical greeks consistent with Gate N units; do not invent greeks where the pipeline does not produce them.

## Dataset Governance (Immutable-by-Version)

- Datasets and expected outputs SHALL be versioned.\
- Any change to inputs or expected outputs requires a version bump, updated manifest entry, new hash, and an explicit PR explanation.\
- Inputs MUST be deterministic and stored in canonical JSON with stable ordering.\
- Expected outputs MUST be canonical JSON and content-hashed for integrity.

## Harness Boundary (Important)

- Gate P may require a separate harness from Gate R because pipeline output schema differs from pricing-level metrics.\
- Gate P harness MUST consume Gate N tolerances for numeric comparisons; Gate P MUST NOT introduce local threshold overrides.\
- Gate P MUST NOT retrofit or modify the Gate R harness; any cross-harness concerns require explicit Gate-level discussion.

## Evidence & CI

- Gate P golden tests SHALL be executed under a dedicated pytest marker (e.g., `pipeline_golden`) — the exact marker name is to be decided in the implementation PR.\
- CI shall run the pipeline golden marker as an explicit step and treat drift as blocking (conceptually; CI changes are part of implementation PRs, not this SSOT).\
- Tests must be runnable locally using the same marker command that CI will use.

## Forward References

- Gate P implementation work follows after this P0 SSOT.\
- Any policy change requires a new Gate or ADR; Gate N remains authoritative and closed.\
- Backtest/scenario/timeline coverage, if desired, requires a dedicated sub-gate under Gate P or a separate Gate.

## ADR References

- ADR-001 (schema_version)\
- ADR-005 (Institutional default bias)\
- ADR-011 (Pricing vs Pipeline regression boundary)
