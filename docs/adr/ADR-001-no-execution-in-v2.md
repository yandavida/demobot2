# ADR-001: No execution in V2

**Status:** Accepted

## Context
V2 is designed as a deterministic, auditable API for ingesting events, producing snapshots, and supporting replay and compliance/audit use cases. Allowing execution (e.g., order placement, trade actions, or any side-effecting operation) would introduce nondeterminism and risk, undermining the auditability and replay guarantees of V2.

## Decision
Execution is explicitly out of scope for V2. All execution logic (such as order placement, trade execution, or feedback from external systems) is deferred to a later stage or a separate, clearly bounded API/service. V2 is strictly limited to event ingestion, validation, and read-only views.

## Consequences
- V2 remains safe for audit, compliance, and deterministic replay.
- No accidental or implicit execution can occur via V2 endpoints.
- Product, opportunity, and execution features must be handled outside V2, in a future phase or separate boundary.

---

*This ADR documents the explicit exclusion of execution from V2, supporting auditability and institutional safety.*
