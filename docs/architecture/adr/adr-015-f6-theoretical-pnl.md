Title: ADR-015 — Gate F6 — Theoretical Portfolio Lifecycle & PnL Segregation

Status
------
PROPOSED

Context
-------
Gate F5 has locked deterministic hedging primitives, numeric policy, and golden governance for pricing-level artifacts. Gate F6 defines the canonical portfolio lifecycle contract and the separation of Theoretical (pricing) MTM surfaces from Institutional/Bank MTM. Determinism and event-driven time semantics remain authoritative (Gate D / ADR-014 already referenced across foundations).

Decision
--------
- Gate F6 SHALL define portfolio lifecycle events and PnL surfaces limited to THEORETICAL MTM only. Institutional MTM (bank-standard, FX institutional conventions, or ledger‑grade MTM) is explicitly OUT OF SCOPE and deferred to Gate F8.

- Theoretical MTM is a deterministic, auditable surface derived from pluggable pricing engines and canonical market snapshots. Pricing engines are inputs only; lifecycle mechanics are model‑agnostic and SHALL NOT contain embedded pricing logic.

- All lifecycle transitions and timestamps are driven exclusively by `event.ts` (contractual event time). Wall‑clock time or implicit timestamps are forbidden in lifecycle logic.

- Invariants (tests‑first) MUST be codified and passing prior to any production release of lifecycle behaviors. The following invariants are required:
  - Realized PnL changes only on explicit realization lifecycle events (close, unwind, exercise).
  - Unrealized PnL changes only as a deterministic function of supplied market snapshots/pricing inputs.
  - No double counting: transitions between unrealized and realized PnL must be explicit and atomic.
  - Aggregation identity: instrument‑level sums equal portfolio‑level totals (bitwise where feasible; otherwise subject to `core.numeric_policy.DEFAULT_TOLERANCES`).

Rationale
---------
- Separating Theoretical MTM from Institutional MTM avoids premature binding to bank conventions (funding, CSAs, credit adjustments) and enables deterministic, testable surfaces useful for downstream strategy and analytics.
- Mandating model‑agnostic lifecycle mechanics improves interoperability: pricing engines may be swapped without changing lifecycle contracts.
- Event‑time semantics ensure reproducibility and auditability across replays and backtests.

Consequences
------------
- Auditability: the Theoretical MTM surface is deterministic and reproducible given the same pricing inputs and market snapshots.
- Any proposal to introduce institutional MTM behaviors (funding, discounting, spreads, reconciliation adjustments, accrual conventions) MUST be introduced via Gate F8 with a dedicated ADR.
- Consumers of Theoretical MTM (strategy, reporting) must be aware this surface is NOT reconciled to any ledger-grade institutional PnL until F8 completion.

Non-Goals (explicit)
--------------------
This ADR does NOT cover:
- Funding, discounting, CSA mechanics, or other funding‑related adjustments.
- Credit adjustments (CVA/DVA), liquidity spreads, or reconciliation adjustments.
- Accrual, carry, or roll conventions tied to institutional accounting.
- Optimization/solver implementations for portfolio construction (these are out of scope).
- Any schema changes, dependency additions, or golden format changes.

Governance & Compliance
-----------------------
- Numeric policy is authoritative: all comparisons, guards, and tolerances SHALL use `core.numeric_policy.DEFAULT_TOLERANCES`.
- Golden / pipeline governance continues to use manifest + SHA256 expected hashes; no format changes allowed by this ADR.
- Tests‑first invariants are mandatory and must appear in unit/integration suites and golden regression harnesses where appropriate.

Extension Points
----------------
- Pricing engines remain pluggable inputs; integration tests must exercise alternative engines if used in production.
- Gate F8 (Institutional MTM) is the designated future gate for ledger‑grade MTM, funding, and reconciliation requirements.

Evidence / References
---------------------
- Numeric policy: `core/numeric_policy.py` and ADR-008.
- Deterministic event time: ADR-014 (Deterministic Event Time and Replay) and Gate D.
- Golden governance: ADR-010 and Gate R documentation.

Status Note
-----------
- This ADR is PROPOSED. Acceptance requires merging this document and the usual Gate approvals. Once accepted, Gate F6 semantics are considered locked until superseded by a formal Gate/ADR.
