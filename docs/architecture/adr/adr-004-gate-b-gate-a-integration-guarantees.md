Title: ADR-004 — Gate B ↔ Gate A Integration Guarantees

Status
------
ACCEPTED

Context
-------
Gate A and Gate B are different stages in the institutional pipeline. Gate B outputs are ingested by Gate A consumers. Integration bugs at this boundary can cause lost persistence, duplicate events, or inconsistent state.

Decision
--------
Gate B SHALL only be considered closed for a change when the following integration-proof invariants are demonstrated during integration testing:

- A new command emitted by Gate B that reaches acceptance (NEW→ACCEPTED) SHALL be persisted by the downstream Gate A storage layer and MUST be retrievable (persist).\
- Reprocessing the same command (reopen→seen=True) after a retry storm SHALL result in exactly one persisted event (idempotent persistence).\
- If downstream reconciliation detects a CONFLICT rejection, that rejection SHALL cause no state mutation upstream; the system MUST not apply partial state changes.

Rationale
---------
- Explicit integration invariants protect against duplication and loss.\
- Idempotent persistence is essential for reliability under retries.\
- Guarding against partial state changes ensures safe rollback and operational clarity.

Consequences
------------
- Integration test suites MUST include end-to-end scenarios that prove persistence, idempotency under retries, and conflict-safe behavior.\
- Gate B change acceptance SHALL depend on documented integration proofs; failing proofs SHALL block closure.\
- Operational runbooks MUST describe how to detect and remediate violations of these invariants.
