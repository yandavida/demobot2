Title: ADR-005 — Institutional Default Bias (Conservative by Default)

Status
------
ACCEPTED

Context
-------
Design and operational ambiguity frequently arise in command semantics, validation choices, and error handling. Ambiguity left unaddressed leads to inconsistent implementations across teams.

Decision
--------
When a choice is ambiguous or underspecified, the default SHALL be the most explicit, conservative, and test-enforced option. Teams MUST prefer conservative semantics that fail-fast and require explicit opt-in for permissive behavior. Any deviation from this conservative default SHALL require a new ADR and explicit test coverage demonstrating safety.

Rationale
---------
- Conservative defaults reduce surprise and limit blast radius for regressions.\
- Requiring explicit ADRs for deviations preserves institutional memory and auditability.\
- Test-enforced deviations enforce discipline and catch regressions early.

Consequences
------------
- Implementers MUST default to explicit checks, strict validations, and explicit opt-ins for leniency.\
- Product teams that request permissive behavior MUST file an ADR and add tests demonstrating safety and monitoring.\
- Reviewers and maintainers SHALL expect stronger scrutiny for opt-out proposals.
