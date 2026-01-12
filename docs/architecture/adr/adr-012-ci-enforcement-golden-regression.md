Title: ADR-012 — CI Enforcement for Golden Regression

Status
------
ACCEPTED

Context
-------
Applies to: Gate R and all future Gates

Golden regression must be enforced as part of continuous integration to detect numeric drift early and deterministically.

Decision
--------
The golden test suite SHALL be executed in CI via a pytest marker (e.g. `-m golden`). CI runs of the golden suite SHALL be blocking on drift: failures in the golden suite shall surface as CI failures and block merges until addressed.

Rationale
---------
- Running the golden suite in CI provides timely detection of numeric drift against canonical datasets.\
- A marker-based invocation ensures the same command can be executed locally by developers to reproduce CI results.\
- Blocking CI on golden drift enforces governance and prevents silent regressions.

Consequences
------------
- CI configuration MUST include an explicit step that runs `pytest -q -m golden` (see `.github/workflows/ci.yml`).\
- Developers MUST be able to run the identical command locally.\
- Golden-suite failures are treated as blocking and require an explicit PR and evidence to change expected outputs.

Evidence / References
---------------------
- CI workflow: `.github/workflows/ci.yml` (golden step added)\
- Harness and marker usage: `tests/golden/test_golden_regression.py`, `pytest.ini` marker registration
