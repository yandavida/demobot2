# ADR-002: Execution Boundary

Status: Proposed

## Context
V2 expands the engine to support execution of compute jobs and streaming ingestion. V1 was strictly offline and batch. V2 must define what "execution" means, and where streaming/ingestion boundaries lie.

## Decision
- "Execution" means running a deterministic compute job (risk/pricing), optionally simulating execution
- Streaming ingestion is allowed, but all data must be validated before state mutation
- Error handling: fail fast on contract violation, best effort on ingestion errors
- No live trading or broker integration unless explicitly planned

## Consequences
- Enables streaming and batch workflows
- Preserves deterministic, auditable core
- Prevents accidental live trading or external execution

## Alternatives Considered
- Allowing live trading (rejected: out of scope)
- No streaming (rejected: limits institutional use cases)

## Validation
- All execution paths are covered by tests
- Streaming ingestion is validated and idempotent
- No code path allows live trading by default
