Title: ADR-008 — Numeric Policy as a First-Class Contract

Status
------
ACCEPTED

Context
-------
Applies to: Gate N — Numeric Policy

The project defines a single-source-of-truth for numeric representation, canonical units, and comparison tolerances used by tests and regression harnesses.

Decision
--------
Numeric policy SHALL be captured as both normative documentation and an SSOT code module. Canonical units for Greeks and base numeric conventions SHALL be defined in policy and consumed by comparison code. Core computations SHALL not perform rounding; tolerances used for comparisons SHALL be centralized in a single `DEFAULT_TOLERANCES` mapping in the policy module.

Rationale
---------
- Embedding policy in an SSOT module ensures machine-readable, auditable policy consumption.\
- Centralized tolerances avoid ad-hoc local thresholds and maintain governance.\
- Avoiding rounding in core computations ensures downstream consumers can apply canonical normalization consistently.

Consequences
------------
- Policy consumers (tests, harness) MUST import the SSOT module (see `core/numeric_policy.py`) for units and tolerances.\
- Core numeric code SHALL not perform policy changes or rounding; policy changes require a Gate-level decision.\
- Comparison logic across golden tests shall use the centralized `DEFAULT_TOLERANCES` only.

Evidence / References
---------------------
- Policy module: `core/numeric_policy.py`\
- Gate N documentation and SSOT: `docs/architecture/gate-n-numeric-policy-v2.md` (if present)\
- Tests consuming policy: tests under `tests/v2/`
