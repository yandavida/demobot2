# ADR — G10 Time Fraction Policy

## Status
Accepted for Gate 10 planning.

## Decision

Gate 10 uses a single year-fraction policy identifier:
- ACT/365F

Policy ID (contract-facing):
- ACT_365F

This policy is mandatory in option contract inputs and must be explicit.

## Rationale

- Determinism: a single policy prevents branch-specific interpretation drift.
- Market convention fit: ACT/365F is a common simple baseline.
- Implementation simplicity: no policy matrix or runtime branching in Gate 10.
- Auditability: policy id is explicit in contracts and test fixtures.

## SSOT Location

Planned SSOT location for Gate 10 implementation:
- Core contracts boundary in the option contract module under core/contracts/

The policy identifier must be validated at contract construction time and serialized unchanged in canonical payloads.

## Test Strategy

Required tests:
- Contract accepts ACT_365F and rejects unsupported policy ids.
- Deterministic serialization preserves policy id and ordering.
- Invariants coverage around expiry/time inputs and policy presence.
- Tolerance usage remains aligned with existing numeric policy hooks where relevant.

## Non-Goals

- No calendar libraries in Gate 10.
- No additional day-count variants in Gate 10.
- No holiday calendar adjustments.
- No business-day rolling rules.
