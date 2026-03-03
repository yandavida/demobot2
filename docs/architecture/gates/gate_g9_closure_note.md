# Gate G9 Closure Note (Through G9.4)

## 1) Objective of Gate 9

Gate 9 establishes a deterministic, institutionally-auditable risk infrastructure layer built on top of the frozen Gate F8 valuation stack.
The objective at this stage is structural reliability and replayability, not risk-measure breadth.

## 2) Scope Covered (G9.1–G9.4)

- **G9.1 — Contracts First**
  - `RiskRequest` versioned contract
  - `ScenarioSpec` deterministic shock definition
  - `ScenarioSet` content-addressed descriptor
- **G9.2 — ScenarioGrid v1**
  - Deterministic Cartesian expansion
  - Stable scenario ordering and scenario IDs
- **G9.3 — Deterministic Repricing Harness**
  - FX-forward-first repricing seam over F8 SSOT
  - Deterministic ordering and rejection rules
- **G9.4 — RiskArtifact v1 Freeze**
  - Canonical output artifact
  - Schema/version + required keys + hash-rule freeze
  - Pinned fixture-based backward compatibility

## 3) SSOT Table

| SSOT Element | Owner | Frozen Rule |
|---|---|---|
| Request versioning | `RiskRequest.schema_version` | Required, supported versions only |
| Snapshot identity | `RiskRequest.market_snapshot_id` / `RiskResult.market_snapshot_id` | Must match exactly |
| Scenario identity | `ScenarioSet.scenario_set_id` / `ScenarioGrid.scenario_set_id` | Content-addressed, deterministic |
| Instrument ordering | `RiskRequest.instrument_ids` | Sorted unique canonical order |
| Scenario ordering | `ScenarioGrid.scenarios` | Lexicographic on `(spot, df_domestic, df_foreign)` |
| Artifact hashing | `RiskArtifact` | Canonical JSON + SHA256 over artifact without `sha256` |

## 4) Mathematical Semantics (Explicit)

For instruments $i \in \{1,\dots,N\}$ and scenarios $s$ (base + shocked):

- Base valuation per instrument: $PV_i(0)$
- Scenario valuation per instrument: $PV_i(s)$

Portfolio aggregates:

$$
PV_{total}(0) = \sum_i PV_i(0)
$$

$$
PV_{total}(s) = \sum_i PV_i(s)
$$

Gate 9 through G9.4 freezes the replayable PV surface only.

- No Greeks in this gate.
- No VaR / ES in this gate.
- No optimization/routing in this gate.

## 5) Determinism Guarantees and Enforcement

Determinism is enforced by design and tests:

- No wall-clock behavior (`datetime.now`, `time.time`) in Gate 9 core risk modules.
- No randomness.
- Scenario expansion is deterministic and ordered.
- Repricing outputs are deterministic for identical inputs.
- Artifacts are canonicalized and content-addressed.
- Pinned fixture hash in G9.4 guards against silent schema/hash drift.

Primary enforcement tests include:
- G9.1 contract validation tests
- G9.2 ordering and ID invariants
- G9.3 repricing determinism and rejection rules
- G9.4 artifact freeze + fixture hash immutability
- G9.A boundary guards and structural consistency proofs

## 6) Out-of-Scope / Non-Goals (Current Stage)

- Greeks/exposure analytics are not implemented here.
- VaR/ES/risk-distribution measures are not implemented here.
- No lifecycle coupling, no strategy coupling, no orchestrator coupling.
- No DB persistence or live provider integrations.

## 7) Extension Points

Planned extension axes (future gates):

- **G9.5 exposures** via deterministic finite differences.
- **Options plug-in seam** (post-forward baseline).
- **Arbitrage/routing integration** in later governance gates.

These extension points must preserve current deterministic and SSOT guarantees.

## 8) Evidence Policy

A slice is considered auditable only with:

- `ruff check .` clean
- `pytest -q` green
- bounded scope and explicit file-set discipline
- fixture hash pin where contract freeze exists (G9.4 fixture SHA256 pinned)

## 9) Final Declaration

Gate 9 Tier 1 risk infrastructure (through G9.4) is considered **closed for this stage** if and only if all structural, boundary, and determinism tests pass.
This closure does **not** claim Greeks, VaR/ES, or optimization capabilities.
