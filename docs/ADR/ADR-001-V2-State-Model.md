# ADR-001: V2 State Model

Status: Proposed

## Context
V2 introduces stateful runtime to the risk engine. V1 was fully stateless and deterministic. V2 must define clear boundaries for stateful entities and transitions, while preserving determinism and auditability.

## Decision
- Entities: Session, Run, QuoteStream, PortfolioSnapshot, ComputeJob
- State transitions are explicit, finite-state, and auditable
- All ingest and compute operations must be idempotent
- No hidden or implicit state transitions
- All state changes must be event-driven and logged

## Consequences
- Enables reproducibility and auditability of all state changes
- Facilitates replay and debugging
- Increases complexity of state management

## Alternatives Considered
- Implicit state via in-memory objects (rejected: not auditable)
- Stateless-only (rejected: cannot support streaming/persistence)

## Validation
- All state transitions are covered by event logs
- Replay from event log must yield identical state
- Freeze tests for state transitions
