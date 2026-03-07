# Contract Registry V2 (Repository-Grounded)

## 1. Purpose of the Registry

This registry defines the current contract boundaries in `demobot2` before options-layer expansion.

For each major contract, it documents:
- what it is
- where it lives
- producer and consumer roles
- stability level (frozen/stable/provisional)
- guard mechanism (tests/CI/schema gates)
- evolution expectations

Scope is current observed repository behavior only (code + tests). No redesign.

## 2. Contract Classification Model

Contract classes used in this repository:
- Runtime contracts
- Financial contracts
- Risk contracts
- Advisory contracts
- Copilot contracts
- Artifact contracts
- Warning / error contracts

Classification notes:
- "Frozen" means explicitly guarded by freeze/invariant tests.
- "Stable by usage" means widely consumed and implicitly stable, but not explicitly frozen by a dedicated freeze test.
- "Provisional" means no strong freeze guarantees and expected evolution.

## 3. Core Runtime Contracts

| Contract | Module / Path | Producer | Consumer | Stability | Guard / Test |
|---|---|---|---|---|---|
| `V2Event` | `core/v2/models.py` | `core/v2/event_store_sqlite.py`, artifact stores (`core/market_data/artifact_store.py`, `core/portfolio/advisory_payload_artifact_store_v1.py`, `core/treasury/copilot_artifact_bundle_store_v1.py`) | `core/v2/replay.py`, `core/v2/orchestrator.py`, event store list/replay tests | Stable by usage | `tests/v2/test_v2_eventstore_contract.py`, `tests/v2/test_v2_sqlite_persistence.py`, `tests/v2/test_v2_d3c_eventstore_tail_replay_restart_safe.py` |
| `Snapshot` | `core/v2/models.py` | `core/v2/snapshot_store_sqlite.py`, `core/v2/orchestrator.py` | `core/v2/replay.py`, `core/v2/session_store_sqlite.py` | Stable by usage | `tests/v2/test_v2_snapshots.py`, `tests/v2/test_v2_snapshot_materialized_view.py`, `tests/v2/test_v2_restart_safe_snapshot.py` |
| `SessionState` | `core/v2/models.py` | `core/v2/orchestrator.py` | `core/v2/replay.py`, read model tests | Stable by usage | `tests/v2/test_v2_invariants.py`, `tests/v2/test_v2_d4_readmodel_contract.py` |
| `MarketSnapshotPayloadV0` | `core/market_data/market_snapshot_payload_v0.py` | API/fixtures + market artifact store put path | FX snapshot resolver, risk/pricing and validation flows | Stable (contract-tested) | `tests/market_data/test_market_snapshot_payload_v0_contract.py`, `tests/finance/test_market_snapshot_guardrails.py`, `tests/architecture/test_adr_006_market_snapshot_determinism_immutability.py` |

## 4. Financial / Pricing Contracts

| Contract | Module / Path | Producer | Consumer | Stability | Guard / Test |
|---|---|---|---|---|---|
| `FXForwardContract` | `core/pricing/fx/types.py` | advisory-to-risk adapter and risk harness setup | `core/pricing/fx/forward_mtm.py`, `core/risk/reprice_harness.py` | Stable (invariant-tested) | `tests/core/pricing/fx/test_fx_forward_mtm_invariants.py`, `tests/core/pricing/fx/test_fx_forward_kernel_seam.py`, `tests/core/pricing/fx/test_fx_pricing_boundary_invariants.py` |
| `FxMarketSnapshot` | `core/pricing/fx/types.py` | `core/market_data/fx_snapshot_resolver_v1.py` | FX pricing + risk repricing harness | Stable (invariant-tested) | `tests/core/market_data/test_fx_snapshot_resolver_v1.py`, `tests/core/pricing/fx/test_valuation_context_invariants.py` |
| `OptionContractV1` | `core/contracts/option_contract_v1.py` | options/risk input construction | `core/risk/reprice_harness.py` options path | Stable (contract-tested) | `tests/core/test_option_contract_v1.py`, `tests/core/risk/test_g10_4_options_harness_flow.py` |
| `BSEuropeanPriceV1` | `core/pricing/bs_ssot_v1.py` | `price_european_option_bs_v1` | `core/risk/reprice_harness.py` (EU options repricing) | Stable by usage | `tests/core/pricing/test_bs_ssot_invariants_v1.py`, `tests/pricing/test_bs_european_known_values.py` |

## 5. Risk Contracts

| Contract | Module / Path | Producer | Consumer | Stability | Guard / Test |
|---|---|---|---|---|---|
| `ScenarioSpec` | `core/risk/scenario_spec.py` | scenario template resolution + direct risk callers | `ScenarioSet`, `ScenarioGrid`, `RiskRequest` | Frozen by gate tests | `tests/core/risk/test_g9_1_scenario_spec_determinism.py` |
| `RiskRequest` | `core/risk/risk_request.py` | advisory/risk orchestration | `core/risk/reprice_harness.py`, `build_risk_artifact_v1` validation | Frozen by gate tests | `tests/core/risk/test_g9_1_risk_request_contract.py` |
| `ScenarioGrid` / `ScenarioKey` | `core/risk/scenario_grid.py` | `ScenarioGrid.from_scenario_set` | `reprice_harness`, `risk_artifact` | Frozen by gate tests | `tests/core/risk/test_g9_2_scenario_grid.py` |
| Risk artifact schema (`pe.g9.risk_artifact/1.0`) | `core/risk/risk_artifact.py` | `build_risk_artifact_v1` | exposures, portfolio surface, advisory summary | Frozen by fixture + hash guards | `tests/core/risk/test_g9_4_risk_artifact_freeze.py` |
| Exposures artifact schema (`pe.g9.exposures_artifact/1.0`) | `core/risk/exposures.py` | `compute_exposures_v1` | advisory/risk read models | Frozen by gate tests | `tests/core/risk/test_g9_5_exposures_v1.py` |
| Portfolio surface artifact schema (`pe.g9.portfolio_surface_artifact/1.0`) | `core/risk/portfolio_surface.py` | `compute_portfolio_surface_v1` | scenario summary and downstream risk consumers | Frozen by gate tests | `tests/core/risk/test_g9_6_portfolio_surface_v1.py` |

## 6. Advisory Contracts

| Contract | Module / Path | Producer | Consumer | Stability | Guard / Test |
|---|---|---|---|---|---|
| `AdvisoryInputNormalizedV1` (+ `AdvisoryExposureRowV1`) | `core/services/advisory_input_contract_v1.py` | `normalize_advisory_input_v1` | advisory read model, payload artifact store, copilot invocation helper | Stable (contract-tested) | `tests/services/test_advisory_input_contract_v1.py` |
| `AdvisoryDecisionV1` | `core/services/advisory_output_contract_v1.py` | `run_treasury_advisory_v1` | explainability pack, report renderer, copilot artifacts | Stable (contract-tested) | `tests/services/test_advisory_output_contract_v1.py`, `tests/services/test_advisory_read_model_v1.py` |
| `ScenarioRiskSummaryV1` | `core/services/scenario_risk_summary_v1.py` | `summarize_scenario_risk_v1` | hedge recommendation, explainability, report | Stable (contract-tested) | `tests/services/test_scenario_risk_summary_v1.py` |
| `HedgeRecommendationV1` | `core/services/hedge_recommendation_v1.py` | `recommend_hedge_ratio_v1` | advisory decision, ladder buckets | Stable (contract-tested) | `tests/services/test_hedge_recommendation_v1.py` |
| `HedgePolicyV1` (+ `PolicyApplicationResultV1`) | `core/services/hedge_policy_constraints_v1.py` | policy templates + policy application | ladder service and policy enforcement | Stable (contract-tested) | `tests/services/test_hedge_policy_constraints_v1.py`, `tests/services/test_policy_templates_v1.py` |
| `RollingHedgeLadderResultV1` (+ config/totals/buckets) | `core/services/rolling_hedge_ladder_v1.py` | `compute_rolling_hedge_ladder_v1` | explainability/report when ladder is supplied | Stable (contract-tested) | `tests/services/test_rolling_hedge_ladder_v1.py` |
| `ExplainabilityPackV1` (+ `ExplainabilityItemV1`) | `core/services/explainability_pack_v1.py` | `build_explainability_pack_v1` | copilot renderer and advisory outputs | Stable (contract-tested) | `tests/services/test_explainability_pack_v1.py` |

## 7. Copilot Contracts

| Contract | Module / Path | Producer | Consumer | Stability | Guard / Test |
|---|---|---|---|---|---|
| `CopilotContextV1` | `treasury_copilot_v1.py` | CLI / API callers | `run_treasury_copilot_v1` validation + resolution | Frozen | `tests/core/treasury/test_treasury_copilot_contract_freeze_v1.py` |
| `TreasuryCopilotRequestV1` | `treasury_copilot_v1.py` | CLI / tests / integrations | Copilot router | Frozen | `tests/core/treasury/test_treasury_copilot_contract_freeze_v1.py` |
| `CopilotArtifactsV1` | `treasury_copilot_v1.py` | advisory invocation + bundle resolution | renderer + CLI follow-up output | Frozen | `tests/core/treasury/test_treasury_copilot_contract_freeze_v1.py` |
| `CopilotAuditV1` | `treasury_copilot_v1.py` | router run/follow-up flow | CLI output + follow-up references | Frozen | `tests/core/treasury/test_treasury_copilot_contract_freeze_v1.py` |
| `TreasuryCopilotResponseV1` | `treasury_copilot_v1.py` | router | CLI renderer and QA agent checks | Frozen | `tests/core/treasury/test_treasury_copilot_contract_freeze_v1.py`, `tests/test_treasury_copilot_cli_v1.py` |

## 8. Artifact / Reference Contracts

| Contract | Module / Path | Producer | Consumer | Stability | Guard / Test |
|---|---|---|---|---|---|
| `artifact_bundle:<id>` decision ref format | `treasury_copilot_v1.py` (`_parse_decision_ref_v1`) | Copilot RUN (`run_treasury_copilot_v1`) | Copilot follow-ups (`resolve_decision_ref_to_copilot_artifacts_v1`) | Stable by usage | `tests/core/treasury/test_copilot_followups_v1.py`, `tests/test_treasury_copilot_cli_v1.py` |
| `portfolio_ref` formats (`artifact:`, `portfolio:`; `inline:` unsupported) | `core/portfolio/portfolio_ref_resolver_v1.py` | callers passing context | copilot resolution layer | Stable by usage | `tests/core/portfolio/test_portfolio_ref_resolver_v1.py`, `tests/core/portfolio/test_portfolio_advisory_payload_resolver_v1.py` |
| Artifact store namespace `__market_snapshot_artifacts__` | `core/market_data/artifact_store.py` | `put_market_snapshot` | `get_market_snapshot` + resolver | Stable by usage | `tests/market_data/test_artifact_store.py` |
| Artifact store namespace `__treasury_advisory_payload_artifacts__` | `core/portfolio/advisory_payload_artifact_store_v1.py` | `put_advisory_payload_artifact_v1` | portfolio ref resolver | Stable by usage | `tests/core/portfolio/test_portfolio_ref_resolver_v1.py` |
| Artifact store namespace `__treasury_copilot_artifact_bundles_v1__` | `core/treasury/copilot_artifact_bundle_store_v1.py` | `put_copilot_artifact_bundle_v1` | follow-up resolution + renderer | Stable (schema-guarded) | `tests/core/treasury/test_copilot_artifact_bundle_schema_v1.py` |
| Bundle payload key schema (`advisory_decision`, `explainability`, `report_markdown`, `scenario_table_markdown`, `ladder_table_markdown`) | `core/treasury/copilot_artifact_bundle_store_v1.py` | Copilot bundle put path | bundle get + follow-up render path | Frozen | `tests/core/treasury/test_copilot_artifact_bundle_schema_v1.py` |

## 9. Warning and Error Contracts

Copilot warnings (warning strings are behavioral contracts):

| Contract | Module / Path | Producer | Consumer | Stability | Guard / Test |
|---|---|---|---|---|---|
| `fx_advisory_executed_v1` | `treasury_copilot_v1.py` | successful RUN path | CLI, QA agent, downstream checks | Frozen with peers (allowlist set) | `tests/core/treasury/test_treasury_copilot_contract_freeze_v1.py` |
| `read_only_followup_v1` | `treasury_copilot_v1.py` | successful follow-up path | CLI, QA agent | Frozen with peers (allowlist set) | `tests/core/treasury/test_treasury_copilot_contract_freeze_v1.py` |
| `resolution_failed_v1` | `treasury_copilot_v1.py` | RUN resolution failure | CLI exit mapping + QA checks | Frozen with peers (allowlist set) | `tests/core/treasury/test_treasury_copilot_contract_freeze_v1.py` |
| `followup_resolution_failed_v1` | `treasury_copilot_v1.py` | follow-up resolution failure | CLI exit mapping + QA checks | Frozen with peers (allowlist set) | `tests/core/treasury/test_treasury_copilot_contract_freeze_v1.py` |
| `intent_not_implemented_v1` | `treasury_copilot_v1.py`, `core/treasury/treasury_copilot_renderer_v1.py` | unimplemented-intent fallback | renderer message path | Stable by usage, not in same allowlist set | `test_treasury_copilot_renderer_v1.py` |

Validation/error allowlist:
- Canonical code set is defined in `core/validation/error_taxonomy.py`.
- Allowlist integrity is guarded by:
  - `tests/core/test_validation_error_codes_allowlist.py`

Current canonical codes include:
- `VALIDATION_ERROR`
- `UNKNOWN_COMMAND_KIND`
- `OUT_OF_ORDER`
- `IDEMPOTENCY_CONFLICT`
- `MISSING_SCHEMA_VERSION`
- `UNSUPPORTED_SCHEMA_VERSION`
- `ILLEGAL_SEQUENCE`

## 10. Freeze / Guard Mechanisms

Contract-family guard map:
- Runtime contracts:
  - `tests/v2/test_v2_eventstore_contract.py`
  - `tests/v2/test_v2_invariants.py`
  - `tests/v2/test_v2_sqlite_persistence.py`
  - `tests/v2/test_v2_sqlite_hygiene.py`
- Financial contracts:
  - `tests/core/test_option_contract_v1.py`
  - `tests/core/pricing/test_bs_ssot_invariants_v1.py`
  - `tests/core/pricing/fx/test_*` invariants suite
- Risk contracts:
  - `tests/core/risk/test_g9_1_*` through `test_g9_6_*`
  - `tests/core/risk/test_g9_a_boundary_guards.py`
  - `tests/core/risk/test_g9_c_certification_guards.py`
- Advisory contracts:
  - `tests/services/test_*_v1.py`
- Copilot contracts and schema:
  - `tests/core/treasury/test_treasury_copilot_contract_freeze_v1.py`
  - `tests/core/treasury/test_copilot_artifact_bundle_schema_v1.py`
  - `tests/core/treasury/test_copilot_followups_v1.py`
- Cross-cutting validation taxonomy:
  - `tests/core/test_validation_error_codes_allowlist.py`

CI enforcement:
- `.github/workflows/ci.yml` (repository baseline CI)
- `.github/workflows/treasury_copilot_qa.yml` (deterministic Copilot QA flow, scheduled and PR-triggered)

Schema/version guards present:
- `core/v2/sqlite_schema.py` (`LATEST_SCHEMA_VERSION = 1` hard guard)
- `core/risk/scenario_spec.py` (`SUPPORTED_SCHEMA_VERSION`)
- `core/risk/risk_request.py` (`SUPPORTED_SCHEMA_VERSION`)
- Artifact schema constants in risk modules (`SCHEMA_NAME`, `SCHEMA_VERSION`)

## 11. Evolution Policy

Contract-family evolution status:

| Contract Family | Current State | Additive Fields Allowed? | Version Bump Required? | Documentation Requirement |
|---|---|---|---|---|
| Runtime (`core/v2/models.py`, SQLite schema) | Stable by usage; DB schema hard-guarded | Not safely in DB schema without migration path | Yes for schema-level changes | ADR/docs update under `docs/ADR/` + architecture references |
| Financial pricing contracts | Stable (contract/invariant tested) | Conservative only; prefer explicit versioning | Yes when semantic/shape changes impact engines | Update finance/risk architecture docs + tests |
| Risk contracts/artifact schemas | Frozen by gate tests | No for frozen schemas without opening new gate/version | Yes (`SCHEMA_VERSION` + tests) | Gate docs under `docs/gates/` + relevant ADR notes |
| Advisory contracts | Stable (service contract tests) | Potentially additive with strong backward compatibility checks | Recommended for non-trivial shape/semantic changes | Update architecture references + service tests |
| Copilot request/response/artifact surfaces | Frozen for dataclass fields and bundle key schema | Not for frozen field/key order without explicit change process | Yes for schema-shape changes | Update `docs/architecture_reference_v2.md` and this registry |
| Warning/error string contracts | Stable, string-matched by behavior | Additions possible but require synchronized tests/consumers | Not numeric versioned; policy-level change | Update tests + docs contract registry |

Policy notes:
- If a contract is "stable by usage" but not formally frozen, treat changes as risky and add explicit freeze guards before expansion.
- For frozen families, additive fields should be treated as breaking unless guarded and versioned intentionally.

## 12. Known Contract Risks

Known risks in current contract surfaces:
- Copilot bundle schema stores `ladder_table_markdown` but not full ladder object; round-trip richness is limited to markdown text.
- Warning strings are operational contracts (CLI/QA logic depends on exact strings), but only a subset has explicit allowlist-style guarding.
- Parser behavior is tied to keyword precedence in `parse_intent_v1`; this affects observed intent contract behavior.
- SQLite runtime uses schema hard-stop (`LATEST_SCHEMA_VERSION = 1`) with no forward migration implementation in-place.
- `intent_not_implemented_v1` is used as a behavior contract, but not included in the same frozen allowlist set as the primary 4 warning codes.
- Some runtime contracts are stable by usage rather than explicit field-order freeze tests.
