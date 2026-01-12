# ADR-014: Deterministic Event Time and Replay

**Status:** ACCEPTED

**Date:** 2026-01-12

## Context

Event-driven session state, snapshotting and replay are core to institutional Finance features. Prior practice mixed server-derived timestamps and ingest-time assignment with canonical payload hashing and deterministic replay semantics. This ADR records the architectural decision to treat event time and replay ordering as a formal contract.

## Decision

We accept Gate D — Deterministic Event Time & Replay Semantics — as the institutional contract for V2 event ingestion and replay. Key points:

- `V2Event.ts` provided by the caller is canonical event time and used for deterministic ordering where present.
- Server-generated wall-clock timestamps (for example `datetime.utcnow()` at ingest) are metadata only and excluded from replay, ordering, and hash inputs.
- Deterministic replay ordering is defined by canonical event time then `event_id` tie-breaker; sequence tokens may be used as a primary ordering when authoritative.
- Canonical hashes are computed from payload data only; metadata fields like created_at/applied_at are excluded.

## Rationale

Institutional replay and state hashing require absolute determinism: identical event sequences (by canonical input fields) must produce identical state and hashes. Making a strict separation between contractual event fields and metadata eliminates wall-clock drift and ensures reproducible snapshots suitable for audit and rollback.

## Consequences

- Implementations must stop using server wall-clock timestamps as ordering or hashing inputs for Gate D-covered flows.
- Event ingestion APIs SHOULD accept `ts` as the authoritative event time; where omitted, the system must label events as non-deterministic or reject them for deterministic flows.
- Any future change to event time semantics requires a new ADR or Gate.

## Related ADRs

- ADR-005 Institutional Default Bias
- ADR-011 Pricing vs Pipeline Regression Boundary
