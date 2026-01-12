# Gate D — Deterministic Event Time & Replay Semantics (V2)

Status: NORMATIVE (Gate D)

Scope
- Applies to event ingestion, event stores, snapshot persistence, replay and state hashing subsystems (V2 event model).
- Contractual for components that produce, persist, or consume `V2Event` and `AppliedEvent` artifacts.

Purpose
- Establish a narrow, institutional contract that guarantees deterministic replay and stable state hashing by removing wall-clock dependency from ordering and canonical payloads.

Contractual Fields vs Metadata
- Contractual (SHALL be stable and canonical):
  - `V2Event.event_id` (string): identity used for deduplication and ordering tie-break.
  - `V2Event.ts` (datetime) when provided as an input by the caller: SHALL be treated as canonical event time and used for deterministic ordering.
  - `V2Event.payload` (dict): the canonical payload used to compute `payload_hash` and any state hashes; payload canonicalization rules (sorted keys, stable serialization) remain in force.

- Metadata (SHOULD NOT influence replay/ordering/hash):
  - `V2Event.payload_hash` as stored for auditing (computed from canonical payload).
  - `Snapshot.created_at`, `V2Event.created_at`, `AppliedEvent.applied_at` — wall-clock timestamps recorded for observability, logging, or auditing only.
  - `EventStore.created_at` and other DB insert timestamps.

Event Time (`event.ts`) — policy
- REQUIRED INPUT when the external caller is the source-of-truth for event time (recommended for production ingestion).
- Derived fallback: systems MAY accept `ts` omitted by caller but then the system MUST treat such derived times as non-deterministic metadata and MUST NOT use them for replay ordering or hashing.
- Sequence-based mode: when an external sequencing token (monotonic sequence or `seq`) is the canonical ordering key, implementations MAY use sequence as primary ordering; `ts` remains tie-breaker only when provided and canonical.

Applied / Created Timestamps
- `AppliedEvent.applied_at` and `Snapshot.created_at` are explicitly METADATA and MUST NOT be considered part of replay semantics or state hash inputs.
- These fields MAY be recorded for audit/tracing but MUST be excluded from all canonical payload/hash computations and MUST NOT influence ordering decisions.

Replay Ordering Rules (no wall-clock dependency)
- Deterministic replay order SHALL be defined as:
  1. Primary: canonical event time if provided by caller (`V2Event.ts`).
  2. Secondary: `event_id` as a stable, unique tie-breaker (lexicographic).
  3. Alternative: when an explicit monotonic sequence token is authoritative, use sequence token as primary, then `event_id` as tie-breaker.
- Under no circumstances SHALL server-generated wall-clock timestamps (e.g., `datetime.utcnow()` at ingest) be used as the authoritative ordering key for replay or hashing.
- When `ts` is absent and no authoritative sequence token exists, events MUST be rejected for deterministic Gate environments or must be ingested only under a clearly labelled non-deterministic operational mode (out of scope for Gate D).

Canonical Hashing
- All canonical hashes (event payload hash, snapshot hash) SHALL be computed from canonicalized payload data only (sorted keys, deterministic serialization). Non-canonical metadata fields MUST be excluded from hash input.

Exclusions / Non-Goals
- Gate D does NOT change pricing or risk calculations.
- Gate D does NOT mandate how audits/logging record `created_at`/`applied_at` — only that they are excluded from deterministic paths.
- Gate D does NOT prescribe implementation details or migration steps.

Governance
- Any change to what is considered contractual event time, or to replay ordering, MUST be introduced through a formal Gate (Gate F) or ADR.
