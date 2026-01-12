Gate R — Closure Note (V2)
===========================

Status: CLOSED
Scope: Pricing-level Golden Regression (per-instrument)

What was delivered

- Deterministic golden regression harness (manifest-driven)
- Versioned, immutable datasets with `sha256` governance
- Canonical expected outputs (units locked by Gate N: vega per 1% IV; theta per calendar day)
- Comparison policy: `core.numeric_policy.DEFAULT_TOLERANCES` only
- CI enforcement via `pytest -m golden`

What is explicitly out of scope

- Portfolio-level valuation (aggregation / FX / margin / VaR)
- Backtest pipelines
- Scenario / risk reports
- Orchestrator / DB-backed services
- IO / clock / persistence paths

R2.2 — Addendum (system-level pipeline)

Status: NOT EXECUTED (Blocked by design, by intent)

Rationale

- The existing harness is explicitly per-instrument and expects Black–Scholes metrics (`price`, `delta`, `gamma`, `vega`, `theta`, `rho`).
- System-level paths (portfolio valuation, aggregation, FX conversion) do exist in the codebase, but their outputs and structure differ from the harness expectations.
- Changing the harness to accept portfolio-level outputs would be a scope change to Gate R and is disallowed by the Gates' "No Retroactive Design" rule.
- Therefore R2.2 (pipeline-level golden regression) is intentionally deferred and must be specified and gated via a new Gate.

Decision

- R2.2 is BLOCKED and deferred to a dedicated future Gate focused on pipeline/system-level golden regression.
- Gate R remains closed and immutable for pricing-level golden regression only.

Evidence map (status summary)

- R0 — SSOT Doc: [docs/architecture/gate-r-regression-harness-v2.md](docs/architecture/gate-r-regression-harness-v2.md)
- R1 — Datasets scaffold: [tests/golden/datasets_manifest.json](tests/golden/datasets_manifest.json) + manifest validator test
- R2 — Expected + harness: golden harness + expected + hashes under `tests/golden/`
- R2.0b — Harness manifest-driven: `tests/golden/test_golden_regression.py` now iterates manifest
- R2.1 — Coverage expansion: dataset pack added under `tests/golden/datasets/` and `tests/golden/expected/`
- R3 — CI integration: `pytest -m golden` enforced in CI (`.github/workflows/ci.yml`)

Forward rule

- Gate R is closed. Any additional golden regression beyond pricing-level requires a new Gate proposal and corresponding PRs.

Checklist before opening Gate P (pointer)

- Ensure R3 PR is merged and CI green
- Ensure Gate R closure note is saved in docs and referenced in PR description
- Ensure there are no open TODOs inside Gate R artifacts
