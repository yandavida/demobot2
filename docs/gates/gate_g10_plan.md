# Gate 10 Plan — European Options Integration

## Objective

Gate 10 introduces a versioned, deterministic European vanilla options path into PortfolioEngine V2.

Scope target:
- European call/put contracts only
- Deterministic request/contract surfaces
- Deterministic option repricing integration in later slices

Hard compatibility rule:
- G9 artifact schemas and hash contracts must remain unchanged.

## T10 Breakdown

### T10.1 — OptionContract v1
- Add versioned option contract type and deterministic serialization.
- Add contract-level validation and invariants tests.
- No repricing integration.

### T10.2 — Risk Input Extension for Options
- Add deterministic mapping path from option contracts into risk request inputs.
- Preserve existing FX-forward-only behavior for legacy callers.
- No schema break in existing G9 artifacts.

### T10.3 — Repricing Harness Options Plug-in
- Add explicit options pricing seam in risk harness.
- Reuse existing SSOT option pricing primitives where available.
- Keep deterministic ordering and replayability guarantees.

### T10.4 — Option Risk Artifact Compatibility + Guards
- Prove no regressions for existing G9 outputs.
- Add minimal guards for deterministic option scenarios and output consistency.
- Pin any new fixture contracts without mutating existing G9 fixtures.

## In Scope
- Versioned options contract surface
- Deterministic serialization and IDs
- Deterministic repricing integration path
- Additional tests and guard rails specific to Gate 10

## Out of Scope
- American/exotic option support
- New VaR/ES measures
- Strategy/lifecycle/hedging redesign
- DB/provider/live data behavior changes
- Any refactor unrelated to Gate 10 slices

## Definition of Done by Slice

### DoD — T10.1
- Versioned European option contract exists
- Deterministic serialize/deserialize roundtrip tests pass
- Deterministic JSON canonicalization tests pass

### DoD — T10.2
- Deterministic contract-to-risk-input adapter exists
- Existing non-option flow remains behaviorally identical
- Targeted compatibility tests pass

### DoD — T10.3
- Harness supports options via explicit seam
- No forbidden cross-layer imports introduced
- Determinism and ordering tests pass

### DoD — T10.4
- Existing G9 artifact schemas unchanged
- Existing G9 fixture hashes unchanged
- New Gate 10 guards/fixes documented and passing

## Evidence and CI Expectations

Every Gate 10 PR must include:
- Current commit hash
- Clean working tree status
- Diff file list vs origin/main
- Targeted lint/test commands and pass summary

Expected CI behavior:
- Targeted Gate 10 tests must pass
- Existing G9 deterministic guard tests must continue to pass
- No fixture churn unless explicitly introduced in a dedicated, approved slice

## Compatibility Guard

Gate 10 must preserve Gate 9 closure guarantees:
- No changes to G9 schema names/versions
- No mutation of G9 hash-pinned fixtures
- No cross-layer contamination into lifecycle/strategy/storage providers
