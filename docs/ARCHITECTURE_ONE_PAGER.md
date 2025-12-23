# ARCHITECTURE_ONE_PAGER.md

## Phase: V1 / Phase 4 (Frozen)

### System Purpose
A deterministic, auditable risk and pricing engine for institutional portfolios. Designed for offline, batch, and audit use. All contracts and core logic are mathematically locked.

### High-Level Module Layout
- **core/contracts/risk_types.py**: Canonical risk dataclasses (Greeks, PortfolioRiskSnapshot, etc.)
- **core/risk/**: Risk engines, VaR/CVaR, unified report, semantics
- **core/scenarios/**: Scenario engine, scenario types, scenario reports
- **core/pricing/**: Pricing context, engines, option types
- **core/market_data/**: Market snapshot, price/fx quotes
- **tests/**: Deterministic, audit-grade test suite

### Data Flow
1. **Input**: Portfolio state, market snapshot, scenario set
2. **Validation**: Type and boundary checks (strict, deterministic)
3. **Core Math**: Pricing, Greeks, scenario deltas, VaR/CVaR
4. **Output**: Unified risk report (all results deterministic)

### Deterministic Computation Model
- No randomness, no stateful execution
- All results are reproducible for a given input
- All contracts and math are frozen (see docs/v1/LOCKS.md)

### Explicit Non-Goals
- No execution, order routing, or stateful workflows
- No persistence or database
- No streaming or real-time analytics

**Audience:** CRO / CTO / Quant / Risk Engineering
