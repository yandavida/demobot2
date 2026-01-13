# ADR Index (SSOT)

This index is normative. Every ADR must appear here with an immutable file path.
Any new ADR must:
- follow ADR template sections (Status / Context / Decision / Consequences),
- be referenced in relevant PRs,
- be added to this index in the same PR (docs-only allowed).

---

## Gate A / Gate B (V2 Foundations)

- **ADR-001 — Command Schema Versioning**
  - Path: `docs/adr/adr-001-command-schema-versioning.md`
  - Evidence: `tests/architecture/test_adr_001_command_schema_versioning.py`

- **ADR-002 — Validation Modes: Strict vs Lenient**
  - Path: `docs/adr/adr-002-validation-modes-strict-lenient.md`
  - Evidence: `tests/architecture/test_adr_002_validation_modes.py`

- **ADR-003 — Error Taxonomy Stability**
  - Path: `docs/adr/adr-003-error-taxonomy-stability.md`
  - Evidence: `tests/architecture/test_adr_003_error_taxonomy_stability.py`

- **ADR-004 — Gate B ↔ Gate A Integration Guarantees**
  - Path: `docs/adr/adr-004-gate-b-gate-a-integration-guarantees.md`
  - Evidence: `tests/architecture/test_adr_004_determinism_reproducibility_guards.py`

- **ADR-005 — Institutional Default Bias**
  - Path: `docs/adr/adr-005-institutional-default-bias.md`
  - Evidence: `tests/architecture/test_adr_005_institutional_default_bias.py`

---

## Gate M — Market Data Boundary (V2)

- **ADR-006 — Market Snapshot Determinism & Immutability**
  - Path: `docs/architecture/adr/adr-006-market-snapshot-determinism-immutability.md`
  - Evidence: `tests/architecture/test_adr_006_market_snapshot_determinism_immutability.py`

- **ADR-007 — Canonical Market Validation Boundary**
  - Path: `docs/architecture/adr/adr-007-canonical-market-validation-boundary.md`
  - Evidence: `tests/architecture/test_adr_007_canonical_market_validation_boundary.py`

---

## Gate N — Numeric Policy (V2)

- **ADR-008 — Numeric Policy as First-Class Contract**
  - Path: `docs/architecture/adr/adr-008-numeric-policy-first-class-contract.md`

- **ADR-009 — Policy vs Coverage Separation**
  - Path: `docs/architecture/adr/adr-009-policy-vs-coverage-separation.md`
  - Evidence: `tests/architecture/test_adr_009_policy_vs_coverage_separation.py`

---

## Gate R — Golden Regression Governance (Pricing-level)

- **ADR-010 — Golden Regression Governance**
  - Path: `docs/architecture/adr/adr-010-golden-regression-governance.md`

- **ADR-011 — Pricing vs Pipeline Regression Boundary**
  - Path: `docs/architecture/adr/adr-011-pricing-vs-pipeline-regression-boundary.md`

- **ADR-012 — CI Enforcement for Golden Regression**
  - Path: `docs/architecture/adr/adr-012-ci-enforcement-golden-regression.md`

---

## Gate P — Pipeline Golden Regression (System-level)

- **ADR-013 — Pipeline Golden Regression Boundary**
  - Path: `docs/adr/adr-013-pipeline-golden-regression-boundary.md`

---

## Gate D — Deterministic Event Time & Replay

- **ADR-014 — Deterministic Event Time and Replay**
  - Path: `docs/architecture/adr/adr-014-deterministic-event-time-and-replay.md`

---

## Cross-References (Non-ADR but normative)
These are not ADRs, but are normative SSOT references frequently cited by ADRs/PRs:
- Codex working protocol: `docs/architecture/codex-working-protocol.md`
- Gate M SSOT: `docs/architecture/gate-m-market-data-boundary-v2.md`
- Gate N SSOT: `docs/architecture/gate-n-numeric-policy-v2.md`
- Gate R SSOT: `docs/architecture/gate-r-regression-harness-v2.md`
- Gate P SSOT: `docs/architecture/gate-p-pipeline-golden-regression-v2.md`
- Gate D SSOT: `docs/architecture/gate-d-deterministic-event-time-v2.md`
