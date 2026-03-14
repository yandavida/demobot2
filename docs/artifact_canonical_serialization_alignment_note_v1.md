# Artifact Canonical Serialization Alignment Note v1

## 1. Purpose
This note records governance status for canonical serialization alignment in the reviewed artifact hashing surfaces.
It establishes the normative interpretation of the observed policy/implementation mismatch and clarifies required governance posture.
This note is governance-focused and does not prescribe implementation steps.

## 2. Reviewed canonicalization surfaces
The reviewed surfaces are:

- **V1 canonical serialization scope**
  - `docs/canonical_serialization_rules_v1.md` defines a narrow, explicit PR-3 scope for `OptionPricingArtifactV1`.
  - `core/contracts/canonical_serialization_v1.py` and `core/contracts/canonical_hashing_v1.py` implement V1 serialization and SHA-256 hashing behavior.
  - `tests/core/test_canonical_serialization_v1.py` and `tests/core/test_canonical_hashing_v1.py` guard deterministic V1 behavior and hash invariants.

- **V2 artifact canonical payload hashing scope**
  - `core/contracts/canonical_artifact_payload_hash_v2.py` defines canonical payload derivation, serialization, and SHA-256 hashing for V2 artifact payloads.
  - `tests/core/test_canonical_artifact_payload_hash_v2.py` guards determinism, order, purity, hash format, and mutation sensitivity for V2 payload hashing.

- **Artifact policy text scope**
  - `docs/artifact_evolution_policy_v2.md` defines artifact addressing and canonical JSON policy for artifact IDs.

## 3. Confirmed alignment issue
A confirmed policy/implementation alignment issue exists in the reviewed V2 path:

- Reviewed V2 policy text specifies canonical JSON with one `ensure_ascii` mode in `docs/artifact_evolution_policy_v2.md`.
- Reviewed V2 implementation in `core/contracts/canonical_artifact_payload_hash_v2.py` serializes with a different `ensure_ascii` mode.
- This is a confirmed policy/implementation alignment issue for the governed artifact canonicalization path.

## 4. Normative interpretation
The following governance interpretation is binding:

- Canonical serialization behavior for a governed artifact path MUST be unambiguous.
- Policy text and implementation MUST agree on canonical serialization parameters.
- Versioned canonicalization policies are acceptable only when:
  - scope is explicit,
  - version boundaries are clear,
  - each scoped policy is internally aligned with its implementation.

## 5. Current status decision
This issue is classified as:

- **confirmed implementation drift**

## 6. Follow-up direction
- Policy/implementation alignment for the reviewed V2 canonicalization path must be restored.
- V1 and V2 canonicalization scopes should remain explicitly separated.
- Future canonicalization rules should be frozen per domain/path with explicit scope, and MUST NOT be inferred loosely across versions.

## 7. Non-negotiables
- Governed canonical serialization parameters MUST be explicit and stable.
- Policy text and implementation MUST NOT diverge on canonical encoding semantics.
- Scoped versioning MUST include clear domain/path ownership.
- Deterministic hashing guarantees MUST remain binding across reviewed governed artifact paths.
