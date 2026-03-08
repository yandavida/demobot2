# Architecture Fix Pack: Options Layer V1

Status: Approved architecture note (documentation-only)
Scope: PortfolioEngine V2 options and derivatives architecture alignment
Applies Before: any options implementation work

## Purpose

This document records the institutional-grade architecture corrections approved for the Options Layer and its integration into PortfolioEngine V2.

These corrections are non-negotiable and must be treated as architectural constraints before coding begins.

## Hard Boundary

This fix pack is architecture documentation only.

It does not:
- change production code
- change runtime behavior
- change persistence schema or migrations
- change module structure
- change CI

## Correction 1: PricingContext Contract Introduction

### Decision
Introduce a formal `PricingContext` contract as the required input boundary for derivatives pricing.

### Rationale
Options pricing currently depends on multiple orthogonal inputs (valuation time, rates, discount factors, conventions, market snapshot semantics). Without a strict context contract, engine calls risk hidden assumptions and cross-layer leakage.

### Required Architectural Properties
- Single, explicit contract object passed to pricing engines.
- Must carry all pricing-relevant conventions in one place.
- Deterministic and serializable.
- No hidden fallback to wall-clock or implicit environment defaults.

### Contract Boundary Rule
Engine selection and engine execution must consume the same context surface; no per-engine ad-hoc contextual inputs.

## Correction 2: Portfolio / Position / PortfolioState Boundary

### Decision
Enforce strict separation between:
- `Position` (atomic holding)
- `Portfolio` (collection/composition)
- `PortfolioState` (time-bound state snapshot used for computation)

### Rationale
Derivatives analytics requires unambiguous ownership of quantities, valuations, and lifecycle status. Mixing entity responsibilities causes incorrect aggregation and unclear risk provenance.

### Required Architectural Properties
- `Position` remains atomic and valuation-addressable.
- `Portfolio` composes positions without mutating pricing semantics.
- `PortfolioState` is the deterministic computation boundary at a specific valuation state.
- Cross-layer consumers must not infer state by reconstructing it from side channels.

### Contract Boundary Rule
Risk/scenario/advisory layers consume `PortfolioState` as input contract; they do not reach into persistence internals to rebuild exposure context.

## Correction 3: Derivative Lifecycle Boundary

### Decision
Define lifecycle as a dedicated architectural boundary for derivative instruments.

### Rationale
Options introduce lifecycle-sensitive behavior (activation, exercise style constraints, expiry handling, post-expiry valuation behavior). Lifecycle logic must not leak into generic pricing or reporting surfaces.

### Required Architectural Properties
- Lifecycle state is explicit, typed, and deterministic.
- Lifecycle transitions are defined as domain transitions, not renderer/UI decisions.
- Expiry and exercise semantics are evaluated in lifecycle/domain boundary before advisory presentation.

### Contract Boundary Rule
Pricing engines price valid lifecycle states; lifecycle validation determines whether pricing is admissible.

## Correction 4: Greeks vs Scenario vs Risk Separation

### Decision
Enforce three distinct analytical layers:
- Greeks analytics
- Scenario repricing analytics
- Risk aggregation/reporting

### Rationale
These outputs are related but not interchangeable. Conflating them causes broken assumptions in risk interpretation and hedging recommendations.

### Required Architectural Properties
- Greeks are sensitivity metrics under local perturbation assumptions.
- Scenario analytics are explicit path/grid repricing outputs.
- Risk layer aggregates approved inputs (Greeks/scenario/PnL) into governed artifacts.
- Advisory output references each layer explicitly without collapsing semantics.

### Contract Boundary Rule
No layer may relabel another layer's output as if it were native output (for example, scenario loss must not be emitted as a Greek).

## Correction 5: Capability-Based Pricing Resolver (Resolver V2)

### Decision
Adopt capability-based `Pricing Resolver V2` for derivatives engine dispatch.

### Rationale
Options support multiple instrument styles and engine families (European vs American, and future extensions). Static or implicit routing is brittle and leads to hidden incompatibilities.

### Required Architectural Properties
- Resolver chooses engine by declared capability matrix.
- Capability checks are explicit and auditable.
- Unsupported combinations fail deterministically with structured errors.
- Resolver must remain isolated from UI/renderer assumptions.

### Contract Boundary Rule
Callers request pricing by contract capability; they do not hardcode engine internals.

## Architectural Integration Notes

This fix pack aligns with existing PortfolioEngine V2 principles:
- determinism
- explicit contracts
- separation of concerns
- freeze/guard before expansion

Integration expectation for options phase:
1. Lock boundary contracts first.
2. Add tests/freeze guards for new contracts.
3. Only then implement engine-level functionality.

## Non-Goals

This document does not:
- define final class/field-level implementation details
- add runtime resolvers
- add options persistence schema
- change current Copilot or advisory runtime behavior

## Implementation Gate Requirement

Before options coding starts, each correction above must be represented by:
- explicit contract/module boundary
- deterministic validation behavior
- test guard coverage

No implementation should proceed if one of the five corrections is missing.

## References

Related architecture references in repository:
- `docs/architecture_reference_v2.md`
- `docs/contract_registry_v2.md`
- `docs/artifact_evolution_policy_v2.md`
- `docs/options_architecture_v1.md`
