# SECURITY_AND_LIMITS.md

## Explicit Limits & Scope Control (V1 Phase 4)

### What is Out of Scope
- No threat model for execution, order routing, or stateful workflows
- No persistence or database guarantees
- No streaming or real-time analytics
- No performance, latency, or scale guarantees
- No PII or sensitive data handling (engine operates on abstracted, non-personal data)

### Validation Posture
- Strict: All inputs are type-checked and validated
- No external state or mutation
- All computation is deterministic and reproducible

### Security Posture
- Engine is designed for offline, batch, and audit use only
- Not suitable for production trading or execution environments
- No external connectivity, no order routing, no stateful execution

### What is Guaranteed
- Deterministic results for a given input
- All contracts and math are frozen (see docs/v1/LOCKS.md)
- No mutation or side effects

---

**For full scope and guarantees, see docs/v1/LOCKS.md and docs/v1/V1_FREEZE.md**
