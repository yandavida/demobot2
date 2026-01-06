Title: ADR-002 — Validation Modes Semantics (Strict / Lenient)

Status
------
ACCEPTED

Context
-------
Validation behavior is used in multiple code paths for both UX and authoritative state decisions. Teams sometimes treat a "lenient" mode as permissive for acceptance; this creates ambiguity and divergence in downstream systems.

Decision
--------
The system SHALL support two validation modes: `strict` and `lenient`. HOWEVER, `lenient` SHALL be limited to presentation and diagnostic concerns only. The semantics for acceptance, rejection, and state mutation MUST be identical between modes: a validation failure that would cause rejection in `strict` MUST also cause rejection in `lenient` when the same invariant is violated. There SHALL be NO partial-apply, NO silent-accept, and NO divergence in authoritative state changes.

Rationale
---------
- Clear separation prevents accidental data corruption when a developer uses `lenient` during development.\
- Diagnostics-oriented leniency (richer messages, non-blocking UI) is valuable, but MUST NOT alter core acceptance semantics.\
- Keeping acceptance semantics uniform simplifies audits and enforcement.

Consequences
------------
- Implementers MUST NOT treat `lenient` as a weaker acceptance rule.\
- Tests and CI MUST exercise both modes for diagnostic output, but acceptance-path tests SHALL target `strict` semantics as the source of truth.\
- Any change that would alter acceptance semantics requires a formal ADR and migration plan.
