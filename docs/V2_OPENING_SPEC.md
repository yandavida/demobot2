# V2_OPENING_SPEC.md

## Scope
V2 introduces stateful runtime, streaming, persistence, and performance features to the institutional risk engine. All V1 math and API behavior remain frozen and auditable.

## What V2 Adds
- Stateful runtime: Sessions, runs, jobs, and event-driven state
- Streaming ingestion and output (QuoteStream, event logs)
- Persistence: append-only event log, snapshots
- Performance: caching, reproducibility, explicit determinism

## What V2 Does NOT Add
- No live execution or broker integration by default
- No trading, order routing, or external execution unless explicitly planned
- No PII or sensitive data handling
- No speculative V2 features outside this spec/ADRs

## V1 Compatibility Contract
- V1 API and math behavior are frozen (see docs/v1/LOCKS.md)
- "Do not touch" list:
  - core/contracts/risk_types.py
  - core/risk/semantics.py
  - core/risk/var_types.py
  - core/risk/var_parametric.py
  - core/risk/var_historical.py
  - core/risk/unified_report_types.py
  - All V1 test contracts and freeze tests
- Any change to locked items requires explicit ADR and PR label

## State Model
- **Entities:**
  - Session: top-level context for a user or process
  - Run: a single deterministic computation
  - QuoteStream: streaming market data/events
  - PortfolioSnapshot: point-in-time portfolio state
  - ComputeJob: atomic risk/pricing task
- **State transitions:** finite-state, explicit (see ADR-001)
- **Idempotency:** all ingest and compute must be idempotent

## Execution Boundary
- "Execution" in V2 means: running a deterministic compute job, optionally simulating execution
- Streaming ingestion: all data validated before state mutation
- Error handling: fail fast on contract violation, best effort on ingestion errors (see ADR-002)

## Persistence Contract
- **Event schema:** event_id, session_id, timestamp, type, payload_hash
- **Storage:** append-only event log, optional snapshots
- **Semantics:** exactly-once for core events, at-least-once for ingestion (see ADR-003)

## Determinism & Reproducibility
- Determinism: all math and state transitions must be reproducible from persisted events
- Caching allowed only if it does not break reproducibility
- Re-run from event log must yield identical outputs (see ADR-004)

## Math Quality Discipline
- Invariants: see ADR-005
- Rounding: explicit policy, no hidden float errors
- Currency/FX: single source per run, no mixed rates
- Testing: property/golden/freeze tests for all math

## Non-Goals
- No live trading, no broker integration, no PII, no speculative V2 features

## Open Questions
- What is the minimal event schema for full replayability?
- How to version contracts and migrations for future V2+?
- What are the performance/caching boundaries for reproducibility?

---

See ADRs for detailed design decisions.
