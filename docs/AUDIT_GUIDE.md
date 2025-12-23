# AUDIT_GUIDE.md

## How to Audit This Engine (V1 Phase 4)

### 1. Run Full Validation
- Run all tests: `pytest -q`
- Check code style: `ruff check .`
- All tests must pass for any change to be accepted

### 2. Confirm Deterministic Behavior
- All results are deterministic for a given input
- No randomness, no stateful execution
- Scenario and VaR/CVaR results are reproducible (see tests/test_unified_risk_report.py)

### 3. Locate Contracts/Schemas
- Canonical contracts: core/contracts/risk_types.py, core/risk/semantics.py, core/risk/var_types.py, core/risk/unified_report_types.py
- All contract paths are listed in docs/v1/LOCKS.md

### 4. Locate Freeze Tests
- Contract freeze: tests/test_v1_contract_freeze.py
- Only RiskContext is present in core/risk/semantics.py (no RiskAssumptions)

### 5. Audit Checklist
1. All tests pass (pytest -q)
2. Lint clean (ruff check .)
3. Contract freeze tests pass
4. Canonical contracts exist and are not duplicated
5. No changes to locked contracts or math
6. UnifiedPortfolioRiskReport contract exists and is frozen
7. Scenario engine is deterministic
8. VaR/CVaR logic is scenario-based and deterministic
9. No stateful execution or persistence
10. No execution/order management logic
11. No streaming or real-time analytics
12. No PII or sensitive data handling
13. All documentation matches code and tests
14. V1 freeze is documented in docs/v1/V1_FREEZE.md
15. Any change to locked items requires new spec, version bump, and review

### 6. What to Inspect
- All contract and math changes must be reviewed against docs/v1/LOCKS.md
- Confirm no duplicate dataclasses (see freeze test)
- Review audit trail in git history

---

**For full institutional audit, see docs/v1/LOCKS.md and docs/v1/V1_FREEZE.md**
