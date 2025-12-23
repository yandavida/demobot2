# ADR-004: Determinism, Caching, and Reproducibility

Status: Proposed

## Context
V2 introduces performance features (caching, streaming) but must preserve determinism and reproducibility. V1 was strictly deterministic and reproducible.

## Decision
- Determinism: all math and state transitions must be reproducible from persisted events
- Caching is allowed only if it does not break reproducibility
- Re-running from event log must yield identical outputs
- No hidden randomness or time-dependence in math outputs

## Consequences
- Enables performance improvements without sacrificing auditability
- Ensures all results are reproducible for audit
- Limits some caching/performance optimizations

## Alternatives Considered
- Unrestricted caching (rejected: breaks reproducibility)
- No caching (rejected: limits performance)

## Validation
- Freeze tests for reproducibility
- Golden tests for event replay
- All caches must be invalidated on relevant state change
