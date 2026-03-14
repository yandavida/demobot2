# Result and Artifact Phase-Scope Note v1

## 1. Purpose
This note records governance status for phase scope of reviewed result and artifact output contracts.
It clarifies current implementation shape, governance interpretation, and required documentation posture.
This note is governance-oriented and does not prescribe implementation changes.

## 2. Reviewed output surfaces
Reviewed surfaces:

- `OptionValuationResultV2` (`core/contracts/option_valuation_result_v2.py`)
- `OptionPricingArtifactV2` (`core/contracts/option_pricing_artifact_v2.py`)
- Phase C canonical measure order (`PHASE_C_CANONICAL_VALUATION_MEASURE_ORDER_V1`)
- Phase D model-direct measure order (`PHASE_D_MODEL_DIRECT_VALUATION_MEASURE_ORDER_V1`)

Supporting governance and certification references reviewed:

- `docs/phase_d_american_policy_freeze_v1.md`
- `docs/contract_registry_v2.md`
- Artifact/result tests in:
  - `tests/core/test_option_pricing_artifact_v2.py`
  - `tests/core/services/test_pricing_artifact_builder_v2.py`
  - `tests/core/services/test_pricing_artifact_export_v2.py`
  - `tests/core/services/test_pricing_artifact_import_v2.py`
  - `tests/core/services/test_pricing_artifact_roundtrip_v2.py`

## 3. Observed implementation shape
Observed implementation behavior is:

- `OptionValuationResultV2` currently accepts both Phase C and Phase D measure orders.
- This indicates intentional code-level sharing across phases within one result contract surface.
- `OptionPricingArtifactV2` wraps that shared result surface by embedding `OptionValuationResultV2` and enforcing artifact identity/hash constraints around it.

## 4. Governance interpretation
The normative interpretation is:

- Shared output surfaces across phases are not inherently invalid.
- When phase-sharing is intentional, shared scope MUST be explicitly frozen in governance documentation.
- In absence of an explicit freeze statement for this shared scope, the current state is a governance ambiguity rather than a confirmed defect.

## 5. Current status decision
This issue is classified as:

- **governance ambiguity / docs clarification needed**

## 6. Follow-up direction
- Governance documentation should explicitly state whether shared result/artifact phase scope is intentional.
- If intentional, the phase-sharing rationale and boundaries should be frozen explicitly.
- If not intentional, future contract-surface separation should be considered explicitly and governed, rather than emerging through drift.

## 7. Non-negotiables
- Phase scope for governed output contracts MUST be explicit.
- Shared cross-phase contracts MUST have frozen rationale and boundaries.
- Phase behavior MUST NOT be inferred implicitly from tests alone.
- Artifact wrappers MUST preserve contract identity and canonical integrity regardless of phase scope choice.
