# Resolver Boundary Governance Note v1

## 1. Purpose
This note establishes normative governance for resolver-layer semantic scope in demobot2.
It clarifies what the resolver layer is permitted and not permitted to do.
This is a governance artifact and boundary-definition document, not an implementation guide.

## 2. Normative role of the resolver layer
The resolver layer is an upstream boundary before pricing and valuation engines.
The resolver layer MUST produce deterministic, governed, engine-facing resolved inputs.
The resolver layer MUST be the legal loading boundary for governed dependencies required before pricing.
The resolver layer MUST remain distinct from pricing-engine computation logic.
The resolver layer MUST remain distinct from persistence implementation details.

## 3. Allowed resolver responsibilities
The resolver layer MAY perform the following responsibilities, provided they are deterministic and governance-anchored:

- Dependency loading through repository abstractions.
- Structural validation of loaded inputs and required fields.
- Consistency checks across loaded governance objects and references.
- Normalization of loaded domain structures into explicit immutable resolved contracts.
- Deterministic assembly of resolved basis and lineage-related fields required by governed contracts.
- Limited upstream derivation required so engines consume already-resolved governed inputs.

These responsibilities are allowed only when behavior is deterministic, auditable, and tied to an explicit governance source.

## 4. Forbidden resolver behaviors
The resolver layer MUST NOT perform the following:

- Direct SQL or persistence-implementation logic.
- Pricing-engine math execution or model-evaluation logic.
- Hidden fallback behavior that is not explicitly governed.
- Ad-hoc policy creation without an explicit governed source.
- Nondeterministic behavior.
- Use of wall-clock time, random input, ambient environment, or hidden mutable state.
- Mutation of loaded source objects as part of resolution.
- Silent repair of invalid upstream states.

Invalid states MUST fail explicitly at boundary validation and MUST NOT be auto-corrected silently.

## 5. Normalization vs governed derivation
### Definitions
Normalization is deterministic transformation of loaded domain data into explicit resolved contract shape without introducing new unguided policy semantics.

Governed derivation is deterministic computation performed upstream of engines that is required to satisfy governed engine-facing contracts and is explicitly anchored to a governance source.

### Governance decision
demobot2 adopts: **loading + validation + normalization + limited governed derivation**.

### Normative interpretation
Normalization is allowed when converting loaded raw domain structures into explicit resolved immutable contracts.

Governed derivation is allowed only when all of the following are true:

- It is required upstream so engines consume already-resolved governed inputs.
- It is tied to an explicit governed policy source, contract rule, or frozen architecture note.
- It is deterministic and reproducible.

Private service-level policy constants alone are NOT a sufficient governance anchor.

## 6. Resolver-owned outputs
The resolver layer MAY own production of governed engine-facing resolved outputs, including:

- Resolved option valuation inputs.
- Resolved convention basis.
- Resolved curve inputs.
- Resolved volatility inputs.
- Deterministic basis/hash lineage-related fields required by governed contracts.
- Additional governed resolved contracts frozen by later phases.

Resolver outputs MUST be immutable-by-contract and deterministic in construction.

## 7. Current governance gaps identified
The following are governance gaps, not confirmed implementation bugs:

- Canonical serialization policy scope is versioned/contextual and SHOULD be documented explicitly by domain and contract surface.
- Some resolver-authored conventions are not yet explicitly linked to `ValuationPolicySet`, `ModelRegistry`, or contract-level governance anchors.

Current examples from reviewed code include:

- Tenor-to-year-fraction conversion.
- FX kernel scalar selection policy.
- Curve interpolation/extrapolation defaults.
- Vol-surface parsing and fallback conventions.
- Lineage string formatting conventions.

These are governance clarification and refactor-candidate areas, not defect claims.

## 8. Follow-up direction
- Docs clarification is needed to make resolver policy anchors explicit by domain.
- Governed policy linkage SHOULD be explicit wherever derivation exists.
- Service-boundary refactor MAY be appropriate for policy-bearing resolver logic.
- Future phases SHOULD preserve engine purity by resolving such semantics upstream.

## 9. Non-negotiables
- Resolver is upstream of engines.
- Engines consume resolved governed inputs only.
- Repository abstractions are the only persistence access path for resolver loading.
- No hidden semantics.
- No nondeterminism.
- No silent repair of invalid states.
- No policy-bearing derivation without explicit governance anchor.
