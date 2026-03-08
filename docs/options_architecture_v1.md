# Options Architecture V1

## 1. Purpose of the Options Layer

The Options layer provides institutional-grade option pricing, scenario risk analysis, and strategy advisory for PortfolioEngine V2.

Primary goals:
- price option instruments deterministically under governed model assumptions
- support multi-leg strategy representation and analysis
- integrate option repricing into the existing scenario-based risk stack
- produce advisory artifacts suitable for decision support and audit

Scope is architecture definition for the options capability surface, not implementation changes.

Governance alignment requirement:
- Options implementation is governance-first and must remain consistent with:
     - `docs/architecture_reference_v2.md`
     - `docs/contract_registry_v2.md`
     - `docs/artifact_evolution_policy_v2.md`
     - `docs/architecture_fix_pack_options_v1.md`
     - `docs/governance_foundations_options_addendum_v1.md`

Pre-implementation foundations required before options coding begins:
- `ReferenceDataSet`
- `ValuationPolicySet`
- `ValuationContext`
- `ValuationRun`
- `ModelRegistry`
- `PortfolioState` as canonical risk input
- lifecycle boundary outside pricing engines
- artifact lineage and method provenance
- repository abstraction boundary in front of SQLite

## 2. Supported Option Types

Supported exercise styles:
- European options
- American options

Exercise style semantics:
- European: exercisable at expiry only
- American: exercisable at or before expiry

The system selects an engine consistent with exercise style and supported model assumptions.

Implementation order rule:
- European vanilla precedes American vanilla.
- American vanilla is conditional on frozen tree-step policy, frozen numerical tolerances, approved model governance, and benchmark/regression pack readiness.

## 3. Pricing Architecture

The pricing architecture is multi-engine by design.

| Engine | Supports | Method |
|---|---|---|
| `BlackScholesEngine` | European | closed-form |
| `BinomialAmericanEngine` | American | CRR binomial tree |

Architecture principles for engine selection:
- explicit engine routing by contract capability
- deterministic inputs and outputs for a given contract + market state
- no hidden fallback to non-governed engines

Resolver governance:
- Resolver logic is capability-based and governed through approved model metadata in `ModelRegistry`.
- Pricing engines are approved models, not arbitrary runtime choices.

## 4. Volatility Model

The options layer requires a volatility surface model.

Surface definition:
- axes: `Strike x Tenor`
- volatility type: lognormal implied volatility

Operational expectation:
- vol surface data is resolved from market snapshot inputs and mapped deterministically to pricing inputs
- missing/invalid volatility data is a validation error, not an implicit default

Valuation-basis boundary:
- `MarketSnapshot` remains immutable market observables only.
- Static conventions and calendars are externalized to `ReferenceDataSet`.
- Model and numerical controls are externalized to `ValuationPolicySet`.

## 5. Mathematical Conventions

Canonical conventions for options pricing and risk in this layer:
- time convention: `ACT/365F`
- pricing framework: forward pricing
- dividend model: continuous yield
- discounting: `exp(-rT)`

These conventions must remain explicit in engine interfaces and reproducible across reruns.

Numerical governance condition:
- American options must not proceed before numerical-policy controls are frozen (tree-step policy, tolerances, convergence and regression controls) under approved model governance.

## 6. Option Contracts

`OptionContractV1` contract fields (architecture-level contract surface):
- `underlying`
- `option_type`
- `strike`
- `expiry`
- `exercise_style`
- `notional`
- `currency`

Contract requirements:
- all required fields must be present and validated before pricing
- contract validation must be deterministic and side-effect free
- exercise style drives engine eligibility

FX options domain completeness requirement:
- currency pair orientation
- base currency and quote currency
- premium currency
- premium payment date
- settlement style
- fixing source and fixing date
- expiry cutoff timezone
- settlement calendars
- domestic curve id and foreign curve id
- volatility quote convention

## 7. Strategy Representation

The options layer uses an N-leg strategy architecture with arbitrary basket support.

Core entities:
- `OptionLeg`
- `StrategyBasket`
- `StrategyRecognizer`
- `StrategyAnalyzer`

Design intent:
- represent any strategy as a basket of legs (not limited to fixed templates)
- detect known structures where possible while preserving generic basket support
- allow advisory/risk output for both recognized and unrecognized baskets

Risk-universe rule:
- Strategy baskets do not create a separate risk universe.
- Basket logic creates hypothetical trades/positions that become hypothetical `PortfolioState`.
- The same pricing/scenario/risk stack is reused for both real and hypothetical portfolio states.

## 8. Greeks Set

Expanded Greeks target set for options analytics:
- Delta
- Gamma
- Vega
- Theta
- Rho
- Vanna
- Volga (Vomma)
- Charm
- Speed
- Zomma
- Color
- Ultima

All Greeks must be reported with explicit units/conventions and deterministic computation policy.

Basis consistency rule:
- Greeks must be aligned to the same valuation basis as PV (`Contract Terms`, `MarketSnapshot`, `ReferenceDataSet`, `ValuationPolicySet`, `ValuationContext`).

## 9. Risk Integration

Options integrate into the existing scenario risk architecture through:
- `Scenario Grid`
- `Repricing Harness`
- `Risk Artifact`

Integration model:
- options are repriced across scenario grid points
- scenario results are included in canonical risk artifacts
- downstream surfaces and summaries consume those artifacts uniformly

Architecture split requirement:
- `ScenarioEngine` shocks market states only.
- `RiskEngine` aggregates valuation outputs and does not generate shocks internally.
- Options Risk V1 institutional default method is `full_repricing`.

## 10. Advisory Output

Options advisory artifact fields:
- `strategy_detected`
- `legs_summary`
- `pricing_engine_used`
- `exercise_style`
- `net_premium`
- `max_profit`
- `max_loss`
- `breakevens`
- `greeks`
- `scenario_risk`
- `hedge_recommendation`

Artifact rules:
- deterministic and content-addressable when persisted
- additive evolution only for future optional sections
- backward-readable by follow-up/rendering consumers

Lineage and provenance expectation:
- advisory and risk artifacts should remain traceable to `ValuationRun` lineage
- method provenance (`pricing_method_tag`, `risk_method_tag`) must be recorded where artifact meaning depends on valuation/risk computation path

## 11. System Flow

Refined options valuation and risk pipeline:

```text
Contract Terms
     + MarketSnapshot
     + ReferenceDataSet
     + ValuationPolicySet
     + ValuationContext
     -> Pricing Resolver
     -> Pricing / Measure Engines
     -> Scenario Engine
     -> Risk Engine
     -> Lifecycle Engine
     -> Artifact Builder
     -> ValuationRun lineage
     -> Event / Artifact Store
```

Operational pipeline detail:

```text
MarketSnapshot
     -> Snapshot Validation (rates, curves, vols)
     -> ReferenceDataSet Resolution (conventions/calendars)
     -> ValuationPolicySet Resolution (model/numerical controls)
     -> ValuationContext Linkage
  -> Vol Surface Resolution (Strike x Tenor, lognormal IV)
  -> Option Contract Validation (OptionContractV1)
  -> Strategy Basket Build (N-leg OptionLeg set)
  -> Strategy Recognition / Analysis
     -> Capability-Based Resolver Selection (ModelRegistry-governed)
       -> BlackScholesEngine (European)
       -> BinomialAmericanEngine (American, CRR)
  -> Per-Leg Pricing + Basket Aggregation
  -> Greeks Computation (expanded set)
  -> Scenario Grid Repricing
     -> Risk Artifact Integration (full_repricing default for Options Risk V1)
     -> Lifecycle Outcome Integration (outside pricing engines)
  -> Advisory Assembly
       -> strategy_detected
       -> legs_summary
       -> pricing_engine_used
       -> exercise_style
       -> net_premium / max_profit / max_loss / breakevens
       -> greeks
       -> scenario_risk
       -> hedge_recommendation
  -> Advisory Artifact Output
```

End-to-end expectations:
- deterministic behavior for identical inputs
- no implicit randomness/time-dependent fields in computed artifact payloads
- compatibility with existing artifact governance and evolution policy

Repository boundary expectation:
- SQLite may remain an early persistence backend, but engines must not depend directly on SQLite.
- Persistence remains behind repository abstraction boundaries.

## 12. Implementation Roadmap (Governance-First)

Phase 0: Governance Foundations
- `ReferenceDataSet`
- `ValuationPolicySet`
- `ValuationContext`
- `ValuationRun`
- `ModelRegistry`
- artifact lineage alignment
- repository boundary note

Phase 1: Option Domain Foundations
- option contracts
- FX options economic-term completeness
- resolver requirements
- valuation dependencies

Phase 2: European Vanilla
- European vanilla pricing
- valuation measures and Greeks
- artifact outputs
- benchmark pack alignment

Phase 3: American Vanilla
- CRR engine path
- tree-step policy freeze
- numerical tolerance freeze
- benchmark/regression validation readiness

Phase 4: Portfolio / Strategy / Risk Integration
- basket to hypothetical portfolio-state flow
- scenario repricing
- risk aggregation artifacts

Phase 5: Lifecycle Integration
- expiry
- exercise
- assignment
- settlement
- post-lifecycle portfolio-state recomputation
