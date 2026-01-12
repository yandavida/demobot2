# Gate R — Regression Harness (V2)

**Status:** OPEN (initial definition)

## Purpose

Gate R provides coverage, regression, and empirical validation. Gate R does NOT define numeric policy or semantics — those are locked in Gate N.

## Preconditions

- Gate M is closed and immutable
- Gate N is closed and immutable
- Gate R relies on Gate N for:
  - units
  - tolerances
  - canonical numeric meaning

## Non-Goals (Explicit)

- No pricing correctness vs external benchmarks
- No policy or semantics changes
- No rounding or numeric model changes
- No live market data or providers
- No performance optimization

## Canonical Output Rules

- All golden outputs MUST be canonical
- Vega is per 1% IV
- Theta is per calendar day
- Canonicalization occurs before freezing expected outputs
- Raw units are forbidden in expected files

## Comparison Policy

- All comparisons use `core.numeric_policy.DEFAULT_TOLERANCES`
- No local tolerances in tests
- No hardcoded numeric thresholds in assertions

## Dataset Governance

- Versioned datasets
- Immutable-by-version rule
- Any change requires:
  - version bump
  - new hash
  - PR explanation
- Deterministic inputs only
- Canonical JSON (stable ordering)

## Expected Outputs Governance

- Expected outputs contain key metrics only
- Expected files are versioned and hashed
- Hashes are used to detect broad drift
- Diffs must be readable and actionable

## Execution Plan (High-Level)

- R1 — datasets scaffold + manifest
- R2 — expected outputs + harness
  - R2.1 — dataset expansion
  - R2.2 — pipeline regression paths (if applicable)
- R3 — CI integration
- R4 — empirical tightening (optional, policy PR)

## Determinism Guarantees

- No clock / env / randomness
- Offline execution only
- Replayable indefinitely

## Evidence & CI

- Gate R tests must be runnable via pytest markers
- CI must fail-fast on numeric drift

## Forward References

- Gate F (Finance) opens only after Gate R is established
- Any policy change requires:
  - a new Gate or
  - a formal ADR
