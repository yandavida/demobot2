# LAYERS_AND_GUARANTEES.md

## Formal Layer Definition (V1 Phase 4)

### 1. Input Layer
- **Responsibility:** Accepts portfolio state, market snapshot, scenario set
- **Inputs:** PortfolioState, MarketSnapshot, ScenarioSet
- **Outputs:** Validated, typed objects
- **Invariants:** All inputs must be deterministic, type-checked
- **Guarantees:** No mutation, no randomness
- **Forbidden:** No external state, no persistence

### 2. Core Math Layer
- **Responsibility:** Pricing, Greeks, scenario deltas, VaR/CVaR
- **Inputs:** Validated objects from input layer
- **Outputs:** Risk results, scenario reports, unified risk report
- **Invariants:** All math is deterministic, reproducible
- **Guarantees:** Mathematical contract freeze (see docs/v1/LOCKS.md)
- **Forbidden:** No engine/model changes in V1

### 3. Output/Reporting Layer
- **Responsibility:** Compose unified risk report for audit
- **Inputs:** Results from core math layer
- **Outputs:** UnifiedPortfolioRiskReport (see core/risk/unified_report_types.py)
- **Invariants:** Output is fully auditable, deterministic
- **Guarantees:** Output contract is frozen in V1
- **Forbidden:** No output format changes in V1

---

## Determinism Guarantees
- All results are reproducible for a given input
- No randomness, no stateful execution
- All contracts and math are frozen (see docs/v1/LOCKS.md)

## Contract Stability Guarantees
- All canonical contracts are locked (see docs/v1/LOCKS.md)
- Any change requires new version and explicit review

## V1 Freeze Boundary
- No changes to contracts, math, or semantics in V1
- Only docs/tests may change

## Out of Scope / Future (V2)
- Execution, order routing, streaming, persistence, performance optimizations, new models

---

**For full details, see docs/v1/LOCKS.md and docs/v1/V1_FREEZE.md**
