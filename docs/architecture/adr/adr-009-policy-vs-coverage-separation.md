Title: ADR-009 — Policy ≠ Coverage Separation Rule

Status
------
ACCEPTED

Context
-------
Applies to: Gate N ↔ Gate R

The repository separates numeric policy (units, tolerances) from regression coverage (golden datasets and harness). This separation is a fundamental governance constraint enforced across the codebase.

Decision
--------
Gate N SHALL define policy and semantics only. Gate R SHALL define coverage and regression artifacts only. No dataset or coverage expansion SHALL be performed inside Gate N. No policy or semantic changes SHALL be introduced inside Gate R. Any change that moves a concern between policy and coverage SHALL require a new Gate and an explicit ADR.

Rationale
---------
- Clear separation prevents accidental policy drift when adding tests or datasets.\
- Enforcing this separation via Gates preserves auditability and reduces coupling between numeric semantics and test coverage.\
- Requiring a Gate and ADR for cross-cutting changes makes governance explicit and reviewable.

Consequences
------------
- Developers MUST not add dataset-level changes to policy PRs.\
- Policy PRs (Gate N) MUST not include coverage artifacts.\
- Any cross-cutting proposal MUST be handled through a Gate proposal and accompanying ADR.

Evidence / References
---------------------
- Gate N artifacts: `core/numeric_policy.py`, tests under `tests/v2/`\
- Gate R artifacts: `tests/golden/*`, `docs/architecture/gate-r-regression-harness-v2.md`
