# Artifact Evolution Policy V2

## 1. Purpose of the Artifact Evolution Policy

Artifact schemas in `demobot2` are part of the runtime contract surface. They must evolve in a controlled way to preserve:
- determinism of outputs and IDs
- backward readability of stored records
- Copilot follow-up integrity via historical `decision_ref`
- audit/replay consistency

This policy is normative for artifact and bundle changes before introducing new artifact types (Options/Greeks/etc.).

Alignment note:
- This policy is additive to `docs/architecture_reference_v2.md`, `docs/contract_registry_v2.md`, `docs/architecture_fix_pack_options_v1.md`, and `docs/governance_foundations_options_addendum_v1.md`.
- Objects such as `ReferenceDataSet`, `ValuationPolicySet`, `ValuationContext`, `ValuationRun`, `ModelRegistry`, `PricingMethodTag`, and `RiskMethodTag` are used with the same terminology and role boundaries defined there.

## 2. Artifact Types in the System

Current artifact families and code locations:
- Market snapshot artifacts:
  - `core/market_data/artifact_store.py`
  - payload contract: `core/market_data/market_snapshot_payload_v0.py`
- Advisory payload artifacts:
  - `core/portfolio/advisory_payload_artifact_store_v1.py`
  - normalized payload contract: `core/services/advisory_input_contract_v1.py`
- Copilot artifact bundles:
  - `core/treasury/copilot_artifact_bundle_store_v1.py`
  - request/response references: `treasury_copilot_v1.py`
- Risk artifacts:
  - `core/risk/risk_artifact.py` (`pe.g9.risk_artifact`)
- Exposures artifacts:
  - `core/risk/exposures.py` (`pe.g9.exposures_artifact`)
- Portfolio surface artifacts:
  - `core/risk/portfolio_surface.py` (`pe.g9.portfolio_surface_artifact`)

All three storage-backed artifact families are persisted via `core/v2/event_store_sqlite.py` using namespace-style `session_id` values.

Lineage scope for valuation/risk artifacts (where applicable):
- `portfolio_state_id` (or equivalent portfolio-state lineage reference)
- `market_snapshot_id`
- `reference_data_set_id`
- `valuation_policy_set_id`
- `valuation_context_id` (when lineage uses `ValuationContext` as a linkage object)
- `valuation_run_id` (canonical run lineage parent)
- `scenario_set_id` (when scenario analysis is involved)
- `software_build_hash`
- `engine_id` / `model_id` (where relevant)
- `pricing_method_tag` (where valuation method provenance is needed)
- `risk_method_tag` (where risk method provenance is needed)

## 3. Artifact Addressing Model

Addressing rule:

```text
artifact_id = sha256(canonical_json(payload))
```

Canonical JSON definition (current implementation):

```python
json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
```

Deterministic serialization requirements:
- stable key ordering (`sort_keys=True`)
- no whitespace-sensitive formatting (`separators=(",", ":")`)
- deterministic field normalization before hashing (for example advisory payload normalization)

Why content-addressed IDs:
- same semantic payload => same ID
- natural idempotency in append flows
- hash-based auditability and replay traceability
- no dependence on wall-clock or mutable sequence IDs

Lineage traceability rule:
- Deterministic IDs are necessary but not sufficient.
- Valuation and risk artifacts must trace to one deterministic valuation lineage basis rather than relying on opaque embedded assumptions.

## 4. Copilot Artifact Bundle Schema

Current bundle structure (frozen key order by test):
1. `advisory_decision`
2. `explainability`
3. `report_markdown`
4. `scenario_table_markdown`
5. `ladder_table_markdown`

Where created:
- `put_copilot_artifact_bundle_v1(...)` in `core/treasury/copilot_artifact_bundle_store_v1.py`
- called from RUN path in `treasury_copilot_v1.py`

Where stored:
- SQLite events via `SqliteEventStore`
- namespace: `ARTIFACT_BUNDLE_SESSION_ID = "__treasury_copilot_artifact_bundles_v1__"`

Reference format:
- `decision_ref = "artifact_bundle:<sha256>"`
- parsed and resolved by `_parse_decision_ref_v1` and `resolve_decision_ref_to_copilot_artifacts_v1` in `treasury_copilot_v1.py`

## 5. Bundle Evolution Rules

Allowed evolution:
- additive keys
- optional sections (nullable/absent-safe)

Forbidden evolution on existing keys:
- renaming keys
- removing keys
- changing semantic meaning of existing keys

Compatibility rule for follow-ups:
- follow-up intents must remain able to render from older bundles
- renderer logic must tolerate missing newly-added keys
- old keys remain authoritative for old `decision_ref` bundles

Compatibility and lineage rule:
- Additive extensions must preserve lineage readability for historical artifacts.
- New provenance fields must be optional and backward-compatible.

## 6. Versioning Strategy

`artifact_schema_version` policy:
- Current Copilot V1 bundle behavior is implicit schema evolution (no explicit version field).
- Risk-family artifacts already use explicit schema identity (`schema.name`, `schema.version`).

Allowed strategies:
- Strategy A: implicit schema evolution (current bundle behavior)
- Strategy B: explicit schema version field (future option)

When version bump is mandatory:
- any breaking semantic change
- key rename/removal
- type contract change for an existing required field
- inability to maintain backward read/render behavior

## 7. Backward Compatibility Guarantees

Guarantee:
- existing `decision_ref` bundles must remain readable indefinitely by follow-up flows.

Implications:
- follow-ups must interpret bundles produced by older runtime versions
- renderers must implement fallback behavior for missing optional fields
- historical payloads must not be mutated in storage

Current compatibility anchor:
- follow-up path resolves stored bundle and renders from available fields (including fallback behavior in renderer)

Valuation lineage anchor:
- `ValuationContext` remains a thin linkage object and is not a substitute for run lineage.
- `ValuationRun` is the canonical parent lineage object for deterministic outputs.
- Market observables, reference conventions, and valuation policy must remain independently traceable (`MarketSnapshot`, `ReferenceDataSet`, `ValuationPolicySet`).

## 8. Determinism Guarantees

Determinism rules:
- stable key ordering in canonical serialization
- canonical JSON encoding for hash computation
- no wall-clock-derived fields in hashed payloads
- no UUID/random fields in hashed payloads
- deterministic normalization before artifact creation

Scenario and lifecycle lineage rules:
- Scenario artifacts must identify scenario basis explicitly (for example `scenario_set_id`) rather than relying on shocked-state ambiguity.
- `ScenarioEngine` and `RiskEngine` responsibilities remain distinct: risk artifacts aggregate scenario valuation outputs and must not hide shock generation assumptions.
- Lifecycle-derived artifacts must remain distinguishable from pure valuation artifacts.

Provenance method rules:
- Pricing provenance and risk provenance must be separately expressible where relevant.
- `pricing_method_tag` values may include: `analytical`, `tree`, `monte_carlo`, `finite_difference`.
- `risk_method_tag` values may include: `full_repricing`, `sensitivity_approximation`, `mixed`.
- Institutional default for Options Risk V1 is `full_repricing`.
- Method provenance must be recorded in artifacts whenever outputs depend on pricing or risk computation path.

Software lineage rule:
- Artifacts that require institutional reproducibility should include software lineage metadata such as `software_build_hash`, implementation version, and engine/model version where appropriate.

How tested today:
- Copilot bundle determinism/shape:
  - `tests/core/treasury/test_copilot_artifact_bundle_schema_v1.py`
- Risk artifact hash/schema freeze:
  - `tests/core/risk/test_g9_4_risk_artifact_freeze.py`
- Market artifact idempotent roundtrip:
  - `tests/market_data/test_artifact_store.py`

## 9. Known Limitations

Current observed gaps:
- ladder object is not stored in bundle; only `ladder_table_markdown` is stored
- `scenario_table_markdown` is not pre-rendered in RUN path (currently `None` in invocation flow)
- bundle read path is O(n) over events in bundle namespace (`get_copilot_artifact_bundle_v1` scans list)
- Copilot bundle has no explicit schema version field yet
- valuation-lineage governance objects are approved in architecture/governance docs but not yet represented as runtime artifact schemas (`ValuationRun`, `ReferenceDataSet`, `ValuationPolicySet`, thin `ValuationContext` linkage)

## 10. Future Extensions

New artifact sections should be additive-only, for example:
- `options_risk_table_markdown`
- `greeks_table_markdown`
- `options_explainability`
- `policy_comparison_report`

Future lineage/provenance additions may include (additive-only, optional):
- `valuation_run_id`
- `reference_data_set_id`
- `valuation_policy_set_id`
- `scenario_set_id`
- `software_build_hash`
- `engine_id` / `model_id`
- `pricing_method_tag`
- `risk_method_tag`

Extension rule:
- only add optional keys
- existing keys remain untouched and semantically stable
- renderer/follow-up logic must tolerate absent extension keys

## 11. Migration Strategy

For breaking schema changes, use explicit namespace/version split, for example:

```text
artifact_bundle_v2:<sha256>
```

Migration handling:
- keep v1 readers for historical bundles
- add parallel v2 writer/reader paths
- avoid in-place mutation/rewrite of persisted artifacts

Why current system avoids migrations:
- artifact stores reuse sealed runtime persistence
- deterministic replay and audit traces are simpler with immutable records
- additive evolution minimizes operational risk

## 12. Engineering Rules

Developer rules for artifact changes:
- never mutate stored artifacts
- treat artifacts as immutable records
- new fields must be optional by default
- rendering and follow-up handlers must support missing fields
- preserve canonical serialization and content-addressed ID behavior
- add or update determinism/freeze guards before merging schema changes
- keep valuation assumptions explicit through lineage references, not hidden payload conventions
- preserve separation between `MarketSnapshot`, `ReferenceDataSet`, `ValuationPolicySet`, thin `ValuationContext`, and canonical `ValuationRun` lineage
- keep lifecycle outputs distinguishable from pricing/risk outputs even when downstream valuation is recomputed
