# Gate F8 Tier 1 Closure Note

Date: 2026-03-02  
Status: **Closed — Tier 1 (Internal Institutional Grade)**

## 1) Objective of Gate F8

Gate F8 establishes a deterministic institutional FX valuation layer that is:
- mathematically explicit,
- reproducible under fixed inputs,
- isolated from lifecycle and strategy concerns,
- auditable as an internal institutional pricing stack.

The Tier 1 objective is valuation correctness and architectural integrity, not broad product surface expansion.

## 2) Architectural Principles Enforced

- **Determinism by construction**: same inputs must produce same outputs.
- **Single Source of Truth (SSOT)**:
  - valuation timestamp and domestic currency are context-authoritative,
  - reporting currency is context-aligned in strict paths,
  - discount factors are explicit market inputs.
- **Strict layer separation**: pricing remains isolated from lifecycle, strategy, and API boundary behavior.
- **No rate-to-DF construction**: rates are not transformed into DF inside Tier 1 pricing.
- **No curve/bootstrap logic**: no curve building, interpolation, or bootstrap subsystem.
- **No wall-clock dependency**: no valuation dependency on runtime clock.
- **No implicit defaults/inference**: required valuation inputs are explicit and validated.

## 3) Mathematical Foundations

### Forward MTM

$$
PV = N_f \cdot DF_d \cdot (F_{mkt} - K)
$$

$$
F_{mkt} = S \cdot \frac{DF_f}{DF_d}
$$

### Swap MTM aggregation

$$
PV_{swap} = PV_{near} + PV_{far}
$$

### Cashflow presentation semantics

- `receive_foreign_pay_domestic` → +N foreign, -N\*K domestic  
- `pay_foreign_receive_domestic` → -N foreign, +N\*K domestic

## 4) Implemented Slices (Chronological)

### F8.1 — Pricing Boundary
- **Purpose**: define immutable boundary contracts for pricing inputs/outputs.
- **Enforced**: explicit contract, snapshot, and result structures with deterministic validation.
- **Explicitly NOT allowed**: lifecycle coupling, strategy coupling, hidden pricing behavior.

### F8.2 — Forward MTM
- **Purpose**: implement institutional forward close-out valuation.
- **Enforced**: formula-consistent PV with explicit market inputs and direction semantics.
- **Explicitly NOT allowed**: inferred rates, hidden normalization, nondeterministic data sources.

### F8.3 — DF Policy Lock
- **Purpose**: freeze DF-only valuation input policy.
- **Enforced**: strictly positive discount factors as explicit inputs.
- **Explicitly NOT allowed**: curve/bootstrap/rate construction inside pricing path.

### F8.M2 — Kernel Extraction
- **Purpose**: preserve a stable computational seam.
- **Enforced**: kernel seam boundary maintained without altering pricing SSOT semantics.
- **Explicitly NOT allowed**: seam leakage into lifecycle or strategy behavior.

### F8.B1 — ValuationContext Hardening
- **Purpose**: enforce context authority at valuation runtime.
- **Enforced**: tz-aware timestamp and explicit domestic currency in strict mode.
- **Explicitly NOT allowed**: wall-clock valuation context, implicit reporting authority.

### F8.B2 — Reporting Contract Explicit
- **Purpose**: make reporting boundaries explicit and auditable.
- **Enforced**: explicit reporting fields and strict context alignment checks.
- **Explicitly NOT allowed**: implicit reporting fallback in strict certified flow.

### F8.B3 — Swap Cashflow View
- **Purpose**: deterministic presentation layer for swap cashflow decomposition.
- **Enforced**: presentation semantics aligned to pricing outputs and context authority.
- **Explicitly NOT allowed**: pricing-core mutation through presentation layer.

### F8.B3.2 — Notional Policy Lock + Runtime Date Proof
- **Purpose**: harden sign/magnitude policy and runtime settlement-date correctness.
- **Enforced**: notional as strictly positive magnitude; direction carries sign semantics; runtime date proof checks.
- **Explicitly NOT allowed**: negative-notional sign encoding and implicit date assumptions.

## 5) Governance Protocol Used

Tier 1 closure was executed under strict governance:
- slice-scoped delivery,
- STOP-on-drift policy,
- mandatory evidence for each slice,
- forbidden token scanning,
- no drive-by refactors,
- deterministic test execution discipline.

## 6) Determinism Guarantees

Tier 1 guarantees include:
- no `datetime.now` valuation dependency,
- no randomness in valuation logic,
- no hidden mutable state reliance,
- snapshot-only valuation inputs,
- explicit valuation context required on strict path.

## 7) Test & Verification Summary

Tier 1 verification includes:
- golden SHA256 reconciliation for hand-calculation tier,
- invariant checks (parity, linearity, symmetry/antisymmetry classes as applicable),
- DF positivity enforcement,
- reporting currency SSOT enforcement,
- runtime settlement-date verification,
- kernel seam validation.

## 8) Tier Classification

### Tier 1 — Internal Institutional Grade (Complete)
Tier 1 certifies deterministic internal institutional valuation behavior, boundary integrity, and audit-ready architecture within defined scope.

### Tier 2 — Bank Reference Grade (Future)
Tier 2 expands Tier 1 with reference-grade hardening (external dataset/reconciliation depth, stress determinism packs, artifact-level invariance hardening), beyond Tier 1 baseline.

## 9) Residual Risk Assessment

Known residual scope gaps after Tier 1 closure:
- no external bank reconciliation set certified,
- no extreme scenario pack certification,
- no dedicated stress harness certification,
- no risk simulation layer in Gate F8 Tier 1 scope.

These are explicit scope boundaries, not Tier 1 compliance defects.

## 10) Final Statement

Gate F8 Tier 1 is formally declared complete as an internal institutional valuation gate: deterministic, architecturally isolated, mathematically explicit, and institutionally defensible within the certified Tier 1 scope.
