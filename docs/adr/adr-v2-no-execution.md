# ADR: Why V2 API does not support execution

## Status
Accepted

## Context
The V2 API is designed as a strict, deterministic, and auditable boundary for ingesting and reading risk and analytics data. It is intentionally limited to ingestion, validation, and read-only audit/reporting endpoints. Execution (e.g., order placement, trade execution, or any side-effecting operation) is explicitly out-of-scope for V2.

## Decision
- **No execution features** are present or planned in V2. This includes any endpoints or commands that would trigger trading, order routing, or external system effects.
- The V2 API is strictly for ingesting events, validating commands, and exposing deterministic, replayable read models for compliance and audit.
- All execution logic, if needed, must be handled in a separate, clearly bounded API or service layer, with explicit review and controls.

## Consequences
- V2 remains safe for audit, compliance, and deterministic replay.
- No accidental or implicit execution can occur via V2 endpoints.
- Product and opportunity views, as well as execution, are out-of-scope and must be handled elsewhere.

---

*This ADR documents the explicit exclusion of execution from V2, supporting auditability and institutional safety.*
