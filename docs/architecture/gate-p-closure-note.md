# Gate P — Closure Note (V2)

**Status:** CLOSED

**Scope:** Pipeline-level Golden Regression (offline fixtures)

## Purpose

Gate P establishes pipeline/system-level regression harness using deterministic fixtures, without modifying numeric policy (Gate N) and without touching pricing-level Gate R.

## Preconditions (Locked)

- Gate M closed & immutable
- Gate N closed & immutable (DEFAULT_TOLERANCES SSOT)
- Gate R closed (pricing-level)
- Gate P executed only on offline fixtures (no DB/providers)

## Deliverables (Evidence Map)

- P0 SSOT: docs/architecture/gate-p-pipeline-golden-regression-v2.md (PR #186)
- P1 datasets scaffold: tests/golden/pipeline/datasets_manifest.json and tests/golden/pipeline/datasets/portfolio_smoke_v1/inputs_v1.json (PR #187)
- P2 expected outputs + hashes + harness test: tests/golden/pipeline/expected/portfolio_smoke_v1/expected_v1.json, tests/golden/pipeline/expected_hashes.json, tests/golden/pipeline/test_pipeline_golden_regression.py (PR #189)
- P3 CI integration: pytest marker registration in pytest.ini and CI step in .github/workflows/ci.yml (PR #190)

## Locked Contracts

- P-INPUT Envelope v1 is fixture-only (NOT a Command)
- Manifest-driven execution
- Expected outputs are canonical (no raw units)
- Comparisons use only `core.numeric_policy.DEFAULT_TOLERANCES`
- Stable ordering requirements (deterministic sorting)
- Offline-only: no clock/env/randomness, no DB-backed services, no live providers

## Explicit Non-Goals

- No DB/orchestrator/service_sqlite paths
- No live market data/providers
- No policy/semantics changes (Gate N)
- No pricing-level expansions (Gate R)
- No performance optimization
- No external benchmark correctness claims

## How to Run

- Local: `pytest -q -m pipeline_golden`
- Full suite: `pytest -q`

## Forward Rule (Normative)

- Gate P will not be extended retroactively.
- Any new pipeline coverage beyond current fixtures requires a new Gate or ADR.
- Any numeric policy/tolerance change requires new Gate/ADR (per institutional governance).

## ADR References

- ADR-005 Institutional Default Bias
- ADR-011 Pricing vs Pipeline Regression Boundary

## Quality Gates (evidence)

- `python -m compileall -q .` — see CI evidence
- `python -m ruff check .` — see CI evidence
- `pytest -q` — see CI evidence
- `pytest -q -m pipeline_golden` — see CI evidence
