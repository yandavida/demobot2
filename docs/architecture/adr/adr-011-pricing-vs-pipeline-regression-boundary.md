Title: ADR-011 — Pricing-Level vs Pipeline-Level Regression Boundary

Status
------
ACCEPTED

Context
-------
Applies to: Gate R / Future Gate P

Gate R's golden harness is intentionally focused on per-instrument pricing metrics. The codebase contains system-level pipeline paths (portfolio valuation, backtests, scenario reports) that were evaluated during Gate R's development.

Decision
--------
Gate R SHALL remain a pricing-level, per-instrument golden regression gate. System/pipeline-level regression is intentionally deferred and blocked by design from Gate R; any pipeline-level golden regression SHALL be scoped and implemented under a separate Gate (e.g., Gate P). This is an explicit governance decision, not a defect.

Rationale
---------
- Keeping Gate R focused on pricing-level comparisons preserves a narrow, verifiable contract between numeric policy and regression coverage.\
- Pipeline-level regressions introduce different failure surfaces (aggregation, FX conversion, IO, ordering) and therefore require separate specification, fixtures, and governance.\
- Deferring pipeline-level golden regression ensures no retroactive scope creep in Gate R.

Consequences
------------
- The existing harness (`tests/golden/test_golden_regression.py`) remains per-instrument and is not extended to validate portfolio-level outputs.\
- Any proposal to add pipeline-level golden datasets or harness changes MUST be introduced via a new Gate and accompanying ADR.\
- R2.2 is considered blocked-by-design and must be addressed by a future Gate-specific ADR.

Evidence / References
---------------------
- Harness: `tests/golden/test_golden_regression.py`\
- Portfolio/system paths examined: `core/services/portfolio_valuation.py`, `core/portfolio/engine.py`, `core/v2/orchestrator.py`\
- Gate R doc: `docs/architecture/gate-r-regression-harness-v2.md`
