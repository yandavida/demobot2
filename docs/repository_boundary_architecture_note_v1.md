# Repository Boundary Architecture Note V1

## 1. Background

PortfolioEngine V2 currently uses SQLite as the deterministic backend for event and artifact persistence.

This is acceptable at the current stage. However, allowing direct SQLite dependency inside financial engine layers would introduce architectural debt by coupling valuation semantics to a specific persistence implementation.

## 2. Architecture Principle

Persistence is a boundary, not a core financial engine dependency.

Financial computation layers must remain storage-agnostic.

## 3. Why This Boundary Is Required

The repository boundary is required to preserve institutional architecture hygiene:

- preserve engine-layer purity for pricing, risk, lifecycle, and advisory semantics
- prevent persistence technology leakage into pricing/risk/lifecycle code paths
- enable future migration to a multi-writer institutional store without rewriting engine behavior
- support replayability and auditability without coupling engine logic to one database implementation
- preserve testability and deterministic behavior by isolating storage mechanics from financial computation

## 4. Repository Boundary Definition

The repository boundary is the architectural layer through which persistence read/write operations occur for core governance and runtime objects.

Persistence operations for the following object families must occur through repository interfaces or equivalent persistence abstractions:

- `MarketSnapshot`
- `ReferenceDataSet`
- `ValuationPolicySet`
- `ValuationContext`
- `ValuationRun`
- `Artifact`
- `LifecycleEvent`
- `PortfolioState`

Engines must consume domain objects and deterministic contracts, not SQL concerns.

## 5. SQLite Positioning

SQLite remains acceptable as the current deterministic persistence backend for the present stage of PortfolioEngine V2.

Architecturally, SQLite is not the platform identity and has known scaling limits in institutional contexts, including:

- single-writer constraints
- future multi-user or service-oriented persistence requirements
- possible future live opportunity and arbitrage workflows requiring stronger concurrency models

This positioning is architectural, not an operational critique of current usage.

## 6. Non-Negotiable Boundary Rules

- pricing engines must not execute SQL directly
- risk engines must not execute SQL directly
- lifecycle engines must not execute SQL directly
- persistence schema details must not leak into domain-engine contracts
- repository abstractions must be the only persistence access path for core financial objects
- future persistence migration must not require rewriting valuation logic

## 7. Interaction With Existing Governance Objects

The repository boundary supports approved governance objects and boundaries by preserving clean lineage and reproducibility semantics:

- `ValuationRun` remains the canonical lineage parent for valuation and risk outputs
- artifact reproducibility remains deterministic and traceable to governed lineage inputs
- `MarketSnapshot` immutability is preserved as a market-observables boundary
- `ReferenceDataSet` immutability is preserved as a static conventions boundary
- `ValuationPolicySet` governance is preserved as the model and numerical policy boundary

## 8. Future Migration Principle

The architecture must preserve migration from SQLite to other persistence backends, including server-backed relational storage or service-backed institutional persistence, without changing pricing/risk/lifecycle engine semantics.

No concrete future database implementation is prescribed by this note.

## 9. Out Of Scope

This architecture note does not:

- replace SQLite now
- implement repositories in code
- define migration scripts
- define runtime infrastructure
- redesign engine modules

## 10. Final Architecture Decision

Decision:
SQLite remains acceptable as the current persistence backend, but only behind a repository boundary.
Core financial engines must remain storage-agnostic.
