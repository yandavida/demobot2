pip install -r requirements.txt
streamlit run app.py

# Institutional Risk & Pricing Engine — V1 Phase 4 (Frozen)

## What this engine is
- Deterministic, auditable risk and pricing engine for institutional portfolios
- Implements: PV, Greeks, scenario engine, historical/parametric VaR & CVaR, unified risk report
- All logic and contracts are mathematically locked (see docs/v1/LOCKS.md)
- Designed for offline, batch, and audit use — not for execution or streaming

## What this engine is NOT
- Not a trading/execution/order management system
- Not a real-time or streaming analytics engine
- Not a persistence or stateful workflow system
- Not a performance-optimized or scalable production system
- Does not handle PII or sensitive data

## Determinism & Freeze Statement
- All results are deterministic for a given input (see docs/LAYERS_AND_GUARANTEES.md)
- V1 Phase 4 is mathematically and contractually frozen (see docs/v1/V1_FREEZE.md)
- Any change to locked contracts or semantics requires a new version and explicit review

## How to Run Tests / Verify Integrity
- Run all tests: `pytest -q`
- Check code style: `ruff check .`
- All tests must pass for any change to be accepted
- Contract freeze tests: see tests/test_v1_contract_freeze.py

## Documentation
- Architecture: docs/ARCHITECTURE_ONE_PAGER.md
- Layer guarantees: docs/LAYERS_AND_GUARANTEES.md
- Audit guide: docs/AUDIT_GUIDE.md
- Security & limits: docs/SECURITY_AND_LIMITS.md
- V1 freeze: docs/v1/V1_FREEZE.md

---

For full institutional audit, see docs/AUDIT_GUIDE.md and docs/v1/LOCKS.md.
