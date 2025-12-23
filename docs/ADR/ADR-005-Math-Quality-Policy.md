# ADR-005: Math Quality Policy

Status: Proposed

## Context
V2 must maintain a high bar for mathematical correctness, determinism, and auditability. V1 established strict invariants and property-based tests. V2 may introduce new math, but must not compromise quality.

## Decision
- Allowed numeric types: float (with explicit rounding), Decimal for currency if required
- Error budgets/tolerances: all tolerances must be explicit and tested
- Monotonicity: where applicable, math must be monotonic and tested
- No hidden randomness or time-dependence in math outputs
- Deterministic ordering: all aggregates must use stable sort keys
- Precision pitfalls: all known issues must be documented and tested
- Invariants:
  - Pure core: all math functions must be referentially transparent
  - Deterministic aggregates: stable sort before summing
  - Currency conversion: single source rate set per run; no mixed-rate within one valuation
  - Idempotent ingest: same event set ⇒ same persisted state
  - Replayability: persisted events replay ⇒ identical outputs (within explicit epsilon)
  - Versioned contracts: schema changes require explicit version bump + migration plan

## Consequences
- Ensures mathematical correctness and auditability
- Prevents hidden errors and non-determinism
- May limit some optimizations

## Alternatives Considered
- Allowing implicit float errors (rejected)
- No property/golden tests (rejected)

## Validation
- Property/golden/freeze tests for all math
- Explicit rounding and error budget tests
- All invariants are covered by tests
