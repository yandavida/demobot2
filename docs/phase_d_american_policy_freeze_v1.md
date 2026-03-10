# Phase D American Vanilla Policy Freeze v1

## Status and Scope

Phase D freezes the institutional policy baseline for American vanilla FX option valuation before any implementation PR begins.

This document is normative and binding for subsequent Phase D implementation PRs.

This PR freezes policy only. It does not introduce engine code, kernel code, resolver logic, artifact logic, contracts, or benchmark fixtures.

## 1. Frozen Engine Boundary: Two Explicit Governed Inputs

Phase D freezes the American engine boundary as exactly two explicit governed inputs:

- `ResolvedFxOptionValuationInputsV1`
- `ResolvedAmericanLatticePolicyV1`

The engine must consume these two inputs only.

No implicit bundling is allowed.

No hidden fusion layer is allowed.

No ungoverned combined context is allowed.

No internal engine-created semantic context is allowed.

Any future fused context requires explicit later governance and explicit versioned contract freeze.

## 2. Frozen Separation: Economic Inputs vs Model Policy

Phase D freezes a hard separation between economic state and model policy.

Market, trade, and economic state is not model policy.

Model policy is not market or economic state.

American lattice policy must remain explicit and separately governed.

Policy must not be smuggled into trade input contracts.

## 3. Frozen Model Family: CRR Only

Phase D freezes model family support to:

- CRR only
- recombining binomial tree only

Phase D does not support:

- Jarrow-Rudd
- Leisen-Reimer
- trinomial
- pluggable model families

Phase D freezes the CRR equations at policy level:

- $u = \exp(\sigma \sqrt{dt})$
- $d = 1 / u$
- $p = \dfrac{\exp((r_{dom} - r_{for})dt) - d}{u - d}$
- discount factor $= \exp(-r_{dom} dt)$

Phase D freezes:

- $dt = T / N$
- $T$ must arrive as upstream-resolved time fraction
- $N$ must arrive as explicit governed step count

## 4. Frozen Step Policy

Step count is explicit.

Step count is resolved upstream.

The engine consumes step count only.

The engine must never derive step count.

The engine must never adjust step count.

The engine must never repair step count.

No adaptive runtime refinement is allowed.

No magic step counts are allowed.

Invalid discretization handling is frozen as reject, not repair:

- no probability clamping
- no silent step inflation
- no hidden fallback model

The following invalid CRR states are out of policy and must be rejected, not repaired:

- `u == d`
- `p < 0`
- `p > 1`
- degenerate CRR parameterization

## 5. Frozen Early Exercise Rule

Phase D freezes the exact decision rule:

exercise iff

$exercise\_value > continuation\_value + EXERCISE\_EPS$

otherwise continue.

Tie goes to continuation.

Near-tie goes to continuation.

Exercise-on-equality semantics is out of policy.

`EXERCISE_EPS` must be governed and centralized in numeric policy SSOT.

## 6. Frozen Node Valuation Order

Phase D freezes backward induction node order exactly as:

1. determine node spot
2. compute intrinsic or exercise value
3. compute discounted continuation value
4. apply frozen exercise decision rule
5. store node value

## 7. Frozen Convergence Policy

Convergence is benchmark and validation only in Phase D.

Convergence is not runtime behavior in Phase D.

Runtime consumes explicit fixed $N$ and runs once.

No adaptive stopping rule is allowed.

No runtime refinement loop is allowed.

No hidden tolerance-triggered extra compute is allowed.

## 8. Frozen Edge-Case Policy

### Near-zero time

If $T \le TIME\_EPS$, do not run the tree.

`present_value = intrinsic_value`.

`time_value = 0`.

### Zero or near-zero volatility

No silent volatility floor is allowed.

No hidden sigma replacement is allowed.

Use an explicit deterministic zero-vol branch.

Discrete exercise behavior follows the governed grid.

### Low step count

Reject if below governed admissible minimum.

No auto-correction is allowed.

### Deep ITM or OTM

No heuristic branches are allowed.

Behavior is handled by the governed model itself.

### Negative rates

Negative rates are allowed.

Admissibility is model and discretization governed, not sign-taboo governed.

## 9. Frozen Measure Policy for Phase D American Vanilla

Phase D measures remain single-trade valuation measures only.

They are not portfolio metrics.

They are not scenario outputs.

They are not basket outputs.

They are not lifecycle outputs.

They are not advisory outputs.

Phase D freezes the official governed measure set for American vanilla single-trade valuation exactly as:

- `present_value`
- `intrinsic_value`
- `time_value`
- `delta_spot_non_premium_adjusted`
- `gamma_spot`
- `vega_1vol_abs`
- `theta_1d_calendar`
- `rho_domestic_1pct`
- `rho_foreign_1pct`

No additional official governed output measures are allowed in Phase D unless explicitly frozen in a later governed PR.

## 10. Frozen Numerical Measure Regime

For Phase D American vanilla, all official Greeks are numerical bump-and-reprice measures.

No analytical official Greek outputs are allowed.

No hybrid-by-convenience regime is allowed.

No tree-direct gamma or internal shortcut may be promoted to official contract output.

Internal tree-local sensitivities, if computed, remain non-governed diagnostics and must not be substituted for official contract measures.

## 11. Frozen Exclusion: Internal Diagnostics vs Official Outputs

Internal tree-local sensitivities, if ever computed for diagnostics, validation, model research, or internal analysis, are not governed output measures.

They must not appear in:

- official result contracts
- official artifacts
- governed valuation measure vocabularies

unless explicitly frozen in a later phase.

## 12. Frozen Theta Roll Path Responsibility

Theta remains defined as:

$PV(t + 1 \text{ calendar day}) - PV(t)$

The theta roll path must be produced by a governed upstream preparation boundary.

The American engine and kernel consume rolled resolved inputs only.

The engine and kernel must not:

- derive calendar rolls internally
- derive day-count rolls internally
- construct internal roll paths
- perform calendaring logic inside pricing path

## 13. Frozen V2 Evolution Minimalism

In Phase D, versioned contract evolution beyond Phase C is permitted only for the minimal result/artifact evolution required to encode first-class provenance and policy traceability for American valuation.

This V2 evolution applies only to the governed result/artifact surface required by Phase D and must not pre-encode future portfolio, scenario, basket, lifecycle, or advisory semantics.

V2 must not pre-encode or anticipate future:

- portfolio semantics
- scenario semantics
- basket semantics
- lifecycle semantics
- advisory semantics

This is a surgical contract evolution policy, not speculative future-proofing.

## 14. Frozen Benchmark Acceptance Policy

CI must not rely on live external benchmark sources.

Benchmark acceptance must be internalized.

Later benchmark packs must be checked in.

Later expected results and hashes must be checked in.

Later acceptance must bind explicit dataset versions, model-policy versions, and tolerance-policy versions.

Required future benchmark coverage regimes include:

- ATM
- ITM
- OTM
- deep ITM
- deep OTM
- near expiry
- low volatility
- zero-vol branch
- negative-rate regimes
- carry-sensitive cases
- clear early-exercise boundary cases

## 15. Frozen Invariant Expectations for Later Phase D PRs

Later implementation and benchmark PRs must satisfy at least:

- `present_value >= intrinsic_value`
- `time_value = present_value - intrinsic_value`
- `present_value >= 0`
- American PV must not be below comparable European PV under aligned inputs
- deterministic rerun identity
- canonical hash stability
- sanity monotonicity where applicable

## Out-of-Scope Guardrail for PR-D0.1

This PR does not authorize implementation.

Any engine, kernel, resolver, artifact, contract, fixture, benchmark-pack, or CI acceptance implementation change is out of policy for PR-D0.1 and must be introduced in subsequent governed PRs.
