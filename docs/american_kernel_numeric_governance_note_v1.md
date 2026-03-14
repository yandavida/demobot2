# American Kernel Numeric Governance Note v1

## 1. Purpose
This note defines the governance interpretation for numeric representation in the governed American kernel path in demobot2.
It clarifies what is currently acceptable, what is not yet governance-frozen, and what requires explicit numeric-policy escalation.
This note is governance-oriented and does not change implementation.

## 2. Current kernel numeric shape
Observed in the reviewed governed path:

- Inputs to `crr_american_fx_kernel_v1` are contract-governed Decimal fields from resolved inputs and policy (`spot`, `strike`, rates, volatility, time, step count).
- Core CRR math executes in float domain (`math.exp`, `math.sqrt`, float probability/discount arithmetic) after explicit Decimal-to-float conversion.
- Node values and outputs are re-materialized to Decimal via explicit float-to-Decimal conversion.
- The engine wrapper (`AmericanCrrFxEngineV1`) remains contract-governed and deterministic in input boundary and output contract mapping.

## 3. Governance question
The governing question is whether Decimal→float→Decimal execution is formally allowed within the governed American kernel path, rather than only tolerated by current implementation and tests.

## 4. Normative interpretation
The following interpretation is binding for current governance reading:

- Current float-backed kernel execution is **not explicitly forbidden** by reviewed governance documents.
- Current float-backed kernel execution is **not explicitly frozen as the normative numeric representation model** either.
- Therefore, numeric representation status for this kernel **requires numeric-policy escalation** to an explicit governance decision.

## 5. Allowed current interpretation
Until numeric-policy escalation is completed, the following is acceptable:

- Deterministic rerun behavior MUST hold for fixed governed inputs.
- Decimal↔float conversion boundaries MUST remain explicit, reviewable, and testable.
- Hidden numeric fallback behavior MUST NOT be introduced.
- Silent runtime switching of numeric representation MUST NOT occur.
- Phase D invariants and benchmark-pack expectations remain binding and MUST continue to pass.

## 6. Forbidden interpretation
The following interpretations are forbidden:

- Float execution in this kernel MUST NOT be treated as automatic approval for all kernels or compute paths.
- Mixed numeric behavior MUST NOT be silently propagated into other governed kernels.
- Benchmark lock and regression fixtures MUST NOT be treated as a substitute for explicit numeric governance policy.

## 7. Follow-up direction
- Numeric policy escalation is required.
- A future governance note or gate SHOULD explicitly classify this kernel as one of:
  - tolerated float-backed implementation,
  - policy-approved numeric representation,
  - temporary implementation pending stricter numeric policy.
- Any future numeric-representation change MUST preserve determinism, Phase D invariant behavior, and benchmark compatibility.

## 8. Non-negotiables
- Governed American engine boundaries MUST remain contract-based and deterministic.
- Numeric representation changes MUST be explicit and governance-authorized.
- Hidden fallback and silent representation switching MUST NOT occur.
- Phase D benchmark and invariant obligations MUST remain binding.
- Numeric-policy scope decisions MUST be documented as authoritative governance artifacts.
