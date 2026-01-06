# ADR Index — Gate B Normative Policies

This folder contains Institutionally-normative Architecture Decision Records (ADRs) that define Gate B contract invariants, validation semantics, and stability guarantees.

ADRs are normative: a documented decision is the source of truth. Deviations require a new ADR and associated tests.

Included ADRs
- ADR-001 — Command Schema Versioning Policy ([adr-001-command-schema-versioning.md](adr-001-command-schema-versioning.md))
- ADR-002 — Validation Modes Semantics (Strict / Lenient) ([adr-002-validation-modes-strict-lenient.md](adr-002-validation-modes-strict-lenient.md))
- ADR-003 — Error Taxonomy Stability Rule ([adr-003-error-taxonomy-stability.md](adr-003-error-taxonomy-stability.md))
- ADR-004 — Gate B ↔ Gate A Integration Guarantees ([adr-004-gate-b-gate-a-integration-guarantees.md](adr-004-gate-b-gate-a-integration-guarantees.md))
- ADR-005 — Institutional Default Bias (Conservative by Default) ([adr-005-institutional-default-bias.md](adr-005-institutional-default-bias.md))

How to propose changes

1. File a new ADR in this folder that references the existing ADR(s) and states the precise invariant you propose to change. Use the same heading order: `Status`, `Context`, `Decision`, `Rationale`, `Consequences`.
2. Changes to contracts (commands, error codes, validation semantics) MUST include a migration plan and tests and SHALL be gated by a new engineering Gate. Changes without an ADR SHALL NOT be accepted.
3. Review the ADR in a PR labeled `docs/adr` and include a short integration test or a reference to an existing test plan that demonstrates safety.

Normative notes
- ADRs in this folder use MUST / MUST NOT / SHALL language intentionally. They are intended to be auditable and machine-searchable.
