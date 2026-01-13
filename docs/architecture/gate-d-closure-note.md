# Gate D — Deterministic Event Time & Replay (V2) — Closure Note

## Status
Gate D — CLOSED.

## Purpose
Gate D locks deterministic replay semantics by making `V2Event.ts` a contractual input for ordering, while treating all wall-clock-derived timestamps as metadata only. This prevents replay drift, unstable ordering, and non-reproducible state evidence when moving into finance features.

## Scope (What is closed)
### Contractual vs Metadata
**Contractual (must be stable and deterministic):**
- `V2Event.event_id`
- `V2Event.ts`
- `V2Event.payload` (and derived `payload_hash`)

**Metadata (allowed to be wall-clock, but MUST NOT influence replay, ordering, hashing, or golden outputs):**
- `Snapshot.created_at`
- `V2Event.created_at` (if present anywhere)
- `AppliedEvent.applied_at`
- DB persistence `created_at/inserted_at` fields

### Replay Ordering Rules (normative)
- Ordering key is **primary**: `V2Event.ts`, **secondary**: `event_id`.
- Server-generated wall-clock timestamps MUST NOT be used as a fallback for `V2Event.ts`.
- Any future behavior that reintroduces wall-clock into contractual ordering is a Gate/ADR-level change, not an incidental refactor.

## Out of Scope (Explicit non-goals)
Gate D does NOT:
- Change pricing math or financial model semantics.
- Change Gate N numeric policy (tolerances, units, rounding).
- Change Gate R (pricing-level golden regression).
- Change Gate P (pipeline/system-level golden regression governance).
- Introduce new schema versions or modify DB layout.
- Add feature flags or environment-based behavioral toggles for determinism.

## Normative References (SSOT)
- Gate doc: `docs/architecture/gate-d-deterministic-event-time-v2.md`
- ADR: `docs/architecture/adr/adr-014-deterministic-event-time-and-replay.md`

## Evidence Index (Implementation PRs)
The following PRs close the concrete determinism blockers identified in the readiness sweep:

1. **PR1 — Require caller-provided `event.ts` + HTTP 400 mapping**
   - Enforces `V2Event.ts` as required input (no wall-clock fallback).
   - Missing `ts` is mapped to **HTTP 400** using the canonical `ErrorEnvelope` (prevents 500).
   - Test-only injection (pytest) provides deterministic `ts` where legacy tests omitted it, with explicit opt-out via header.

2. **PR2 — Unify `AppliedEvent.applied_at = event.ts`**
   - Live ingest path sets `applied_at` from the contractual event timestamp (`event.ts`).
   - Eliminates wall-clock variance in applied logs, while keeping `applied_at` as metadata (non-contractual).

3. **PR3 — Structural regression guard: no wall-clock fallback**
   - Adds a focused structural test that fails if wall-clock fallback patterns for `event.ts` reappear in `service_sqlite.py`.

## Locked Rules (Non-negotiables)
- `V2Event.ts` is **contractual** and must be provided by the caller for deterministic ingestion.
- No server-side wall-clock fallback is permitted for `V2Event.ts`.
- All wall-clock timestamps remain **metadata only** and must never influence:
  - replay ordering
  - hashing inputs
  - golden comparisons
  - contract outputs
- Any change to these rules requires an ADR update and explicit Gate review.

## Verification (Operational)
Minimum verification for Gate D:
- `make ci` (ruff → mypy → pytest)
- `pytest -q`
- `pytest -q -m golden`
- `pytest -q -m pipeline_golden`

## Result
Gate D is closed with deterministic event time and replay guarantees, and with regression enforcement that prevents future reintroduction of wall-clock fallback behavior.
