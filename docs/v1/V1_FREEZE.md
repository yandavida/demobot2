# V1_FREEZE.md

## Purpose of V1
Institutional Offline Risk & Pricing Engine — provides deterministic, auditable risk and pricing analytics for portfolios, supporting regulatory and institutional requirements.

## What is Included
- Present Value (PV) calculations (per-unit, per-contract)
- Greeks (mathematical derivatives, aggregated)
- Scenario engine (deterministic shocks, scenario reports)
- Historical and Parametric VaR/CVaR (scenario-based, delta_pv_abs)
- Unified Portfolio Risk Report (audit-ready composition)

## What is Locked
- All canonical contracts and types (see LOCKS.md for paths)
- Core risk semantics (PV, Greeks, scenario, VaR/CVaR logic)

## What Remains Open for V2
- Execution and order management
- Realtime and streaming analytics
- Performance optimizations
- Additional pricing/risk models
- Persistence, stateful workflows

## Change Policy
Any change to locked items requires:
- New specification
- Version bump plan (V2+)
- Explicit review and approval
