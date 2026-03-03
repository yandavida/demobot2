# Gate 9 Closure — Tier-1 Deterministic Risk Infrastructure

## Executive Summary

Gate 9 delivers deterministic, replayable, hash-locked Risk Infrastructure.

## Scope Covered

- G9.1 Risk Contracts
- G9.2 ScenarioGrid
- G9.3 Repricing Harness (FX Forward)
- G9.4 RiskArtifact Freeze
- G9.5 Exposures v1 (Finite Difference Spot Delta)
- G9.6 Portfolio Surface v1

## Mathematical Guarantees

- Per-instrument scenario PV is deterministic: `PV_i(s)`.
- Portfolio scenario PV is additive: `PV_total(s) = Σ_i PV_i(s)`.
- Finite-difference spot delta is defined as `Δ_i = (PV_i(+h) - PV_i(-h)) / (2*h*S)` and per-pct form as `(PV_i(+h) - PV_i(-h)) / (2*h)`.
- Scenario loss is defined as `L(s) = PV_total(s) - PV_total(0)`.
- Ranking is deterministic by `(loss asc, scenario_id asc)`.

## Determinism Guarantees

- No wall-clock dependency.
- No randomness.
- Content-addressed scenario IDs.
- Canonical JSON hashing.
- Decimal values encoded as strings.
- Permutation invariance with respect to instrument ordering.

## Hash-Pinned Artifacts

- RiskArtifact v1 fixture SHA256 (`tests/core/risk/_data/g9_risk_artifact_v1_fixture.json`):
  `fd7f108c82fd0f3835564ad5777eee101b5f9c514769c151809f01f773f5097d`
- ExposureArtifact v1 fixture SHA256 (`tests/core/risk/_data/g9_exposures_v1_fixture.json`):
  `9eafb0f9c25297556bc307d52cfd736bc9760528d2a0d76cda33c3f8c3a16f8d`
- PortfolioSurfaceArtifact v1 fixture SHA256 (`tests/core/risk/_data/g9_portfolio_surface_v1_fixture.json`):
  `99cfbf2e9528f2489b0e34ec5bf59eb4c47628eb9169f4efd9b6e61269a96bce`

## Explicit Non-Goals

- No VaR/ES
- No Gamma/Vega
- No optimization
- No execution logic
- No stochastic sampling

## Extension Path

- Gate 10 — Options Plug-in
- Gate 11 — Opportunity Engine
- Gate 12 — Risk Measures (VaR/ES)

## Certification Statement

"Gate 9 Tier-1 Deterministic Risk Infrastructure is CLOSED and CERTIFIED."