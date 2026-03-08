# Governance Foundations Options Addendum V1

## 1. Background

PortfolioEngine V2 is intended to become a deterministic, institutional-grade derivatives strategy and risk platform.

The current architecture direction remains valid and is already documented in:
- `docs/architecture_reference_v2.md`
- `docs/contract_registry_v2.md`
- `docs/artifact_evolution_policy_v2.md`
- `docs/options_architecture_v1.md`
- `docs/architecture_fix_pack_options_v1.md`

This document is an addendum only. It does not replace or redefine the architecture already defined in those references.

The architecture review conclusion is that the platform may proceed, but governance and lineage foundations must be formalized before Options implementation begins.

## 2. Review Outcome

Architecture direction: APPROVED

Options implementation: CONDITIONAL

Decision: GO, WITH CONDITIONS.

PortfolioEngine V2 may proceed toward the Options Layer only after governance and lineage foundations are explicitly formalized.

## 3. Governance Gap Identified

The current architecture correctly separates:
- pricing
- Greeks
- scenario generation
- risk aggregation
- lifecycle state transitions

However, explicit control boundaries are still missing between:
- market observables
- reference conventions
- valuation policies
- model governance
- numerical policy

Without these control boundaries, `ValuationContext` risks becoming overloaded and non-governable.

## 4. Governance Foundations To Introduce

### 4.1 ReferenceDataSet

`ReferenceDataSet` is an immutable, versioned dataset that contains reference conventions, including:
- calendars
- holiday rules
- day-count conventions
- business-day adjustment rules
- settlement conventions
- fixing source identifiers
- exercise conventions
- instrument taxonomy mappings

`ReferenceDataSet` is separate from `MarketSnapshot`.

### 4.2 ValuationPolicySet

`ValuationPolicySet` is the governance object that defines valuation policy and model configuration, including:
- model family
- engine policy
- numerical method
- tolerances
- precision policy reference
- calibration recipe identifier
- validation status

This object governs model selection and numerical controls.

### 4.3 ValuationContext

`ValuationContext` is a thin linkage object that references the full valuation basis. Example fields:
- valuation_timestamp
- market_snapshot_id
- reference_data_set_id
- valuation_policy_set_id
- pricing_currency
- reporting_currency
- run_purpose

`ValuationContext` must remain minimal and traceable.

### 4.4 ValuationRun

`ValuationRun` is the parent lineage object for deterministic valuation outputs.

A `ValuationRun` links:
- portfolio_state_id
- market_snapshot_id
- reference_data_set_id
- valuation_policy_set_id
- software_build_hash
- scenario_set_id
- run_timestamp

Every artifact must reference a `ValuationRun`.

## 5. Model Governance Layer

Introduce `ModelRegistry` as an architecture governance component.

`ModelRegistry` records metadata such as:
- model_id
- semantic_version
- implementation_version
- validation_status
- owner
- approval_date
- benchmark_pack_id
- known limitations

Pricing resolver decisions must rely on approved model metadata.

## 6. Numerical Policy Governance

A rule such as "no floating-point arithmetic" is not sufficient by itself.

The architecture must explicitly formalize:
- precision context
- rounding mode
- convergence rules
- tree-step policy
- regression tolerances
- approved math implementations

American options must not be implemented before these numerical policies are frozen.

## 7. Persistence Boundary

SQLite is acceptable for early deterministic artifact persistence.

However:
- engines must not depend directly on SQLite
- persistence must sit behind a repository abstraction
- future migration to a multi-writer store must be possible without engine changes

## 8. FX Options Domain Completeness

FX option contracts must explicitly support:
- currency pair orientation
- base and quote currency
- premium currency
- premium payment date
- settlement style (deliverable or NDF)
- fixing source
- fixing date
- expiry cutoff timezone
- settlement calendars
- domestic curve id
- foreign curve id
- volatility surface quote conventions

## 9. Refined Institutional Architecture View

Refined architecture flow:

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

Responsibility boundaries:
- Contract Terms: instrument and strategy terms only
- MarketSnapshot: market observables only
- ReferenceDataSet: conventions and reference rules only
- ValuationPolicySet: model and numerical policy governance only
- ValuationContext: thin linkage object for a specific run basis
- Pricing Resolver: capability and policy-based engine selection
- Pricing / Measure Engines: valuation and measures under approved policy
- Scenario Engine: deterministic scenario generation and shock mapping
- Risk Engine: aggregate risk outputs and risk artifacts
- Lifecycle Engine: state transition and lifecycle admissibility
- Artifact Builder: deterministic output packaging
- ValuationRun lineage: traceability parent for all run outputs
- Event / Artifact Store: immutable persistence of run records and artifacts

## 10. Impact On Options Program

Options implementation must follow these governance steps first:
- GF-1 Governance Foundations Addendum
- GF-2 Contract Registry Alignment
- GF-3 Architecture Reference Update
- GF-4 Artifact Evolution Policy Alignment
- GF-5 Options Roadmap Refactor
- GF-6 Repository Boundary Architecture Note
- GF-7 FX Options Contract Preparation
- GF-8 Closure Note

Options implementation begins only after these steps are approved.

## 11. Out Of Scope

This addendum does not implement:
- options pricing engines
- Monte Carlo models
- PDE models
- exotic options
- XVA or CVA
- execution connectivity
- arbitrage runtime engine

## 12. Final Decision

Decision: GO, WITH CONDITIONS.

PortfolioEngine V2 may proceed toward the Options Layer once governance, lineage, model registry, and persistence boundary foundations are in place.
