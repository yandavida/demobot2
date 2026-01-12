# Gate N — Numeric Policy (V2) — Closure Note

**Status:** CLOSED

## Summary

Gate N is closed. Numeric semantics and comparison policy for PortfolioEngine V2 are locked: representation labels, canonical units, and tolerance-driven comparison rules are finalized for this gate stage.

## Deliverables

- N0 SSOT: docs/architecture/gate-n-numeric-policy-v2.md
- N1 Policy module: core/numeric_policy.py
- N2 Units invariants tests: tests/v2/test_gate_n_units_invariants.py
- N3 Golden micro stability: tests/v2/test_gate_n_numeric_stability_golden_micro.py
- Note: Tolerances are pinned in `core/numeric_policy.py` (wide-first initial values).

## Locked Guarantees

- Canonical units: Vega per 1% IV; Theta per calendar day
- No rounding in core computations
- Comparisons are policy-driven via `DEFAULT_TOLERANCES` (SSOT)
- Golden micro tests assert canonical outputs (via `to_canonical_greeks`)
- Unit drift is guarded by invariants and golden micro tests

## What is explicitly NOT covered

- Pricing correctness vs external reference data
- Large regression datasets and harnesses (Gate R)
- Institutional FX MTM pricing formulas (separate Gate)
- Performance optimization

## Evidence Index (commands executed at closure)

```bash
python -m compileall -q .
python -m ruff check .
pytest -q
```

All quality gates are green at closure.

## Forward Plan

- Gate R (regression harness + dataset-driven regression tests) will open next and rely on Gate N guarantees.
- Gate F (further formalization) will open only after Gate R establishes empirical baselines.
