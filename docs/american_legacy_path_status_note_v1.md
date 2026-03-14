# American Legacy Path Status Note v1

## 1. Purpose
This note defines governance status for legacy versus governed American option valuation paths in demobot2.
It clarifies which path is authoritative for Phase D semantics and which path is not.
This note is governance-oriented and does not change implementation.

## 2. Reviewed paths
Reviewed path categories:

- Governed Phase D American path:
  - resolved-contract engine path centered on `AmericanCrrFxEngineV1`
  - governed inputs: `ResolvedFxOptionValuationInputsV1` and `ResolvedAmericanLatticePolicyV1`
  - governed output surface: `OptionValuationResultV2`
- Legacy parallel utility path:
  - `core/pricing/american_greeks.py`
  - float-input finite-difference helper using legacy binomial pricing utility path

## 3. Governance classification
Governance classification is as follows:

- `american_greeks.py` is not part of the governed Phase D American contract path.
- `american_greeks.py` operates as a legacy/parallel utility path.
- `american_greeks.py` MUST NOT be treated as authoritative for Phase D governed semantics.

## 4. Normative implications
The following implications are binding:

- Governed American semantics MUST be sourced from the resolved-contract engine path defined for Phase D.
- Legacy helper paths MUST NOT be treated as equivalent to governed contract paths by implication.
- Absence of explicit deprecation MUST NOT be interpreted as governance approval or contract authority.

## 5. Current status decision
`american_greeks.py` status is classified as:

- deprecation candidate

## 6. Follow-up direction
- Documentation clarification is needed to prevent ambiguity between governed and legacy American paths.
- Future governance SHOULD explicitly decide one of:
  - deprecate,
  - quarantine as legacy utility,
  - replace by governed path.
- No new governed semantics SHOULD be inferred from `american_greeks.py`.

## 7. Non-negotiables
- Phase D American governance MUST remain contract-driven.
- Governed inputs/outputs MUST remain authoritative over legacy utility behavior.
- Legacy paths MUST NOT define or override governed semantics.
- Implicit equivalence between legacy and governed paths MUST NOT be assumed.
- Governance status MUST be explicit in architecture/contract documentation.
