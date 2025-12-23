# ADR-003: Persistence Contract

Status: Proposed

## Context
V2 introduces persistence: event logs and snapshots. V1 was stateless. V2 must define event schema, storage semantics, and idempotency.

## Decision
- Event schema: event_id, session_id, timestamp, type, payload_hash
- Storage: append-only event log, optional snapshots
- Semantics: exactly-once for core events, at-least-once for ingestion
- All state changes must be reconstructible from event log

## Consequences
- Enables full replay and audit
- Facilitates debugging and recovery
- Requires careful event schema/versioning

## Alternatives Considered
- No persistence (rejected: cannot support streaming/stateful workflows)
- Mutable state (rejected: not auditable)

## Validation
- Replay from event log yields identical state
- Freeze tests for event schema and replay
- Event log is append-only, never mutated in place
