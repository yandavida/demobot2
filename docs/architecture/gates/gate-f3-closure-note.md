---
title: "Gate F3 — European Options (Black–Scholes) — Closure Note"
status: CLOSED
date: 2026-01-14
---

# Gate F3 — European Options (Black–Scholes) — Closure Note

Status: CLOSED

Date: 2026-01-14 (Asia/Jerusalem)

Scope
-----

- In scope: European Black–Scholes pricing and greeks (price, delta, gamma, vega, theta, rho) as implemented and exercised by the repository's pricing harness.
- Conventions locked: continuous dividend yield `q` supported; vega canonicalized to per 1% IV; theta canonicalized to per calendar day.

Out of scope
------------

- American option pricing, early exercise models, IV solvers, and broad MTM/portfolio-level changes.
- Hedging strategies, arbitrage engines, and external integration changes.

What was delivered
------------------

- F3.1 — Invariants & Stability
  - Added `tests/finance/test_black_scholes_invariants.py` which encodes: arbitrage bounds, put-call parity, monotonicity, and finite-difference stability checks. FD step rules are deterministic and derived from the numeric SSOT tolerances (`core.numeric_policy.DEFAULT_TOLERANCES`).

- F3.2 — Golden Dataset (canonical)
  - Added `tests/golden/datasets/bs_canonical/inputs_v1.json` and the pinned expected outputs in `tests/golden/expected/bs_canonical/expected_v1.json`.
  - Manifest entry and input SHA256 were recorded in `tests/golden/datasets_manifest.json` and `tests/golden/expected_hashes.json`.

- F3.3a — Golden Rerun Determinism Guard
  - Added `tests/golden/test_golden_rerun_determinism.py` which regenerates the expected serialization for `bs_canonical` and asserts byte-for-byte equality with the checked-in `expected_v1.json` (using the same header fields and serializer settings).

Evidence (summary)
-------------------

All commands below executed on `main` at closure time and observed green results:

- `make ci` — PASS
- `pytest -q` — 673 passed, 1 skipped
- `pytest -q -m golden` — PASS
- `pytest -q -m pipeline_golden` — PASS
- `pytest -q tests/architecture` — PASS

Artifacts and pointers
----------------------

- `tests/finance/test_black_scholes_invariants.py`
- `tests/golden/datasets/bs_canonical/inputs_v1.json`
- `tests/golden/expected/bs_canonical/expected_v1.json`
- `tests/golden/test_golden_rerun_determinism.py`

Next gate
---------

Gate F4 is planned to address American options and richer MTM engines. F4 will follow the same tests-first, gated approach: add guard tests and canonical datasets before any production math changes. No F4 work is included in this PR.

Notes
-----

This closure note documents the scope and artifacts of Gate F3 and provides concise evidence and pointers for auditors and reviewers. The ADR index is updated to reference this closure note.
