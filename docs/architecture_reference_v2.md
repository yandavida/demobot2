# Architecture Reference V2 (Repository-Grounded)

**Repository:** `demobot2`  
**Scope:** PortfolioEngine V2 platform architecture as implemented in code today  
**Status:** Authoritative reference for current state; documentation-only refresh

## 1. System Purpose

PortfolioEngine V2 is a deterministic risk, pricing, and advisory platform with auditable artifacts and replayable persistence.

Current platform capabilities include:
- Deterministic pricing and risk computation (`core/pricing/`, `core/risk/`)
- Stateful V2 runtime with SQLite event/snapshot persistence (`core/v2/`)
- FX advisory orchestration and explainability (`core/services/`)
- Treasury Copilot V1 orchestration, follow-up retrieval, and CLI automation (`treasury_copilot_v1.py`, `core/treasury/`, `scripts/`)

What it is not:
- Not a live execution/routing platform by default
- Not a free-form AI decision system
- Not an architecture with "no persistence"

Obsolete assumption explicitly corrected:
- **"No persistence or database" is obsolete and false for current repository state.**

## 2. Architectural Principles

Determinism:
- Canonical JSON hashing and stable identifiers are used broadly (`core/v2/models.py`, artifact stores)
- Gate-level deterministic checks and reproducibility tests exist under `tests/architecture/`, `tests/f8/`, `tests/core/risk/`

SSOT (Single Source of Truth):
- Numeric tolerances and units are centralized in `core/numeric_policy.py`
- Core contracts are versioned and guarded by freeze/invariant tests

Freeze before expansion:
- Gate artifacts and contracts are frozen before adding scope (`G9`, `F8`, treasury contract freeze tests)
- Schema version guards exist (`core/v2/sqlite_schema.py`, request/schema version tests)

Separation of concerns:
- Core domain logic in `core/`
- API transport in `api/`
- CLI and orchestration scripts in `scripts/`
- Documentation and ADR governance in `docs/`

CI is law:
- Repository CI and treasury QA workflow enforce checks (`.github/workflows/ci.yml`, `.github/workflows/treasury_copilot_qa.yml`)
- Workflow includes deterministic stable IDs and artifact upload

## 3. Repository Architecture Map

Top-level architecture map:

```text
/workspaces/demobot2
|- core/
|  |- v2/                  # runtime state, event store, snapshots, replay
|  |- pricing/             # BS, american, FX pricing kernels/types
|  |- risk/                # scenario spec/grid, repricing, risk artifacts
|  |- market_data/         # snapshot contracts + artifact storage/resolution
|  |- portfolio/           # portfolio aggregation + advisory payload refs
|  |- pnl/                 # realized/unrealized/theoretical PnL
|  |- services/            # FX advisory contracts/orchestration/explainability
|  |- treasury/            # Copilot bundle storage/resolution/renderer
|  |- contracts/           # canonical contract surfaces (option/money)
|  |- validation/          # taxonomy and command/workflow validation
|- treasury_copilot_v1.py  # Copilot V1 router and orchestration seam
|- api/                    # FastAPI layers (v1, v2)
|- scripts/                # CLI + deterministic QA runner
|- tests/                  # contract freezes, invariants, integration guards
|- docs/                   # ADRs, gates, architecture references
```

Layer responsibilities:
- `core/v2/`: persistence and replay runtime (`event_store_sqlite.py`, `snapshot_store_sqlite.py`, `orchestrator.py`)
- `core/pricing/`: instrument valuation engines and math contracts (`bs_ssot_v1.py`, `pricing/fx/forward_mtm.py`)
- `core/risk/`: scenario expansion, repricing harness, content-addressed risk artifacts (`risk_artifact.py`, `exposures.py`, `portfolio_surface.py`)
- `core/services/`: advisory read models, templates, recommendation/policy/ladder/explainability/report surfaces
- `core/treasury/` + `treasury_copilot_v1.py`: Copilot V1 request/response contract, resolution and follow-up retrieval

## 4. Runtime and Persistence Model

Persistence is active and central.

SQLite runtime model:
- DB path policy: `core/v2/persistence_config.py`
- Event append/replay: `core/v2/event_store_sqlite.py`
- Snapshot/session stores: `core/v2/snapshot_store_sqlite.py`, `core/v2/session_store_sqlite.py`
- Schema guard: `core/v2/sqlite_schema.py` (`LATEST_SCHEMA_VERSION = 1`)

Artifact stores currently implemented:
- Market snapshot artifacts: `core/market_data/artifact_store.py`
  - session namespace: `__market_snapshot_artifacts__`
- Advisory payload artifacts: `core/portfolio/advisory_payload_artifact_store_v1.py`
  - session namespace: `__treasury_advisory_payload_artifacts__`
- Copilot artifact bundles: `core/treasury/copilot_artifact_bundle_store_v1.py`
  - session namespace: `__treasury_copilot_artifact_bundles_v1__`

Content-addressed identifiers:
- Artifact IDs are SHA256 of canonical JSON payloads (`json.dumps(sort_keys=True,separators=(',',':'),ensure_ascii=False)`)
- Utility and hashing primitives: `core/v2/models.py`

Reference formats:
- `decision_ref` format in Copilot follow-ups:
  - `artifact_bundle:<artifact_id>`
  - parsed by `_parse_decision_ref_v1` in `treasury_copilot_v1.py`
- `portfolio_ref` formats in resolver:
  - `artifact:<artifact_id>`
  - `portfolio:<portfolio_id>`
  - `inline:` currently rejected as unsupported
  - resolver: `core/portfolio/portfolio_ref_resolver_v1.py`

Runtime/persistence flow:

```text
Input IDs/refs
  -> resolver layer (snapshot/policy/scenario/portfolio)
  -> advisory or risk computation
  -> canonical payload
  -> SHA256 artifact_id
  -> append-only SQLite events row under namespace session_id
```

## 5. Core Financial Engine

Pricing:
- BS SSOT: `core/pricing/bs_ssot_v1.py`
- European/american seams: `core/pricing/engines/bs_european.py`, `core/pricing/engines/binomial_american.py`
- Contract and type surfaces: `core/pricing/types.py`, `core/pricing/option_types.py`

FX pricing:
- FX forward MTM and seam kernels: `core/pricing/fx/forward_mtm.py`, `core/pricing/fx/kernels.py`
- FX swap valuation: `core/pricing/fx/swap_mtm.py`, `core/pricing/fx/swap_types.py`
- FX valuation context and contracts: `core/pricing/fx/valuation_context.py`, `core/pricing/fx/types.py`

Lifecycle / PnL:
- Theoretical/realized/unrealized modules: `core/pnl/theoretical.py`, `core/pnl/realized.py`, `core/pnl/unrealized.py`
- Portfolio breakdown and attribution surfaces: `core/pnl/portfolio_breakdown.py`

Risk infrastructure:
- Request/spec/grid contracts: `core/risk/risk_request.py`, `core/risk/scenario_spec.py`, `core/risk/scenario_grid.py`
- Repricing harness: `core/risk/reprice_harness.py`
- Frozen artifacts: `core/risk/risk_artifact.py`, `core/risk/exposures.py`, `core/risk/portfolio_surface.py`
- Unified report and VaR surfaces: `core/risk/unified_report.py`, `core/risk/var_historical.py`, `core/risk/var_parametric.py`

Market data:
- Snapshot payload contract: `core/market_data/market_snapshot_payload_v0.py`
- Snapshot identity and validation: `core/market_data/identity.py`, `core/market_data/validation.py`
- FX snapshot resolver seam: `core/market_data/fx_snapshot_resolver_v1.py`

Numeric policy:
- Units, tolerances, metric classes: `core/numeric_policy.py`

## 6. FX Advisory Pipeline

Primary modules:
- Input normalization contract: `core/services/advisory_input_contract_v1.py`
- Exposure validation helper: `core/services/exposure_validation_v1.py`
- Scenario templates: `core/services/scenario_templates_v1.py`
- Policy templates: `core/services/policy_templates_v1.py`
- Advisory orchestration: `core/services/advisory_read_model_v1.py`
- Recommendation: `core/services/hedge_recommendation_v1.py`
- Ladder service: `core/services/rolling_hedge_ladder_v1.py`
- Explainability pack: `core/services/explainability_pack_v1.py`
- Report rendering: `core/services/advisory_report_v1.py`

Observed orchestration path:

```text
Advisory payload
  -> normalize_advisory_input_v1
  -> build_risk_request_from_advisory_v1
  -> reprice_fx_forward_risk (G9 harness)
  -> summarize_scenario_risk_v1
  -> recommend_hedge_ratio_v1
  -> AdvisoryDecisionV1
  -> explainability/report renderers
```

Notes:
- The advisory stack is implemented and test-covered (`tests/services/test_*_v1.py`)
- Ladder service exists as reusable component but is not currently wired in Copilot RUN invocation path

## 7. Treasury Copilot V1

Primary modules:
- Router/contracts: `treasury_copilot_v1.py`
- Resolution layer: `core/treasury/copilot_resolution_v1.py`
- Invocation seam (FX advisory): `invoke_fx_advisory_pipeline_v1` in `treasury_copilot_v1.py`
- Artifact bundle store: `core/treasury/copilot_artifact_bundle_store_v1.py`
- Follow-up renderer: `core/treasury/treasury_copilot_renderer_v1.py`
- CLI: `scripts/treasury_copilot_cli_v1.py`
- Deterministic QA runner: `scripts/copilot_qa_agent_v1.py`
- CI workflow: `.github/workflows/treasury_copilot_qa.yml`

Intent parser and request model:
- Intent enum includes:
  - `RUN_FX_HEDGE_ADVISORY`
  - `EXPLAIN_FX_DECISION`
  - `SHOW_SCENARIO_TABLE`
  - `SHOW_HEDGE_LADDER`
  - `COMPARE_POLICIES`
- Parser is keyword and priority based (`parse_intent_v1`)

Follow-up model:
- RUN stores artifacts and emits `audit.as_of_decision_ref`
- Follow-up intents resolve decision ref to stored bundle
- Follow-ups are read-only and emit warning `read_only_followup_v1`

Copilot flow sketch:

```text
Question + Context
  -> parse_intent_v1
  -> validate_context_for_intent_v1
  -> resolve_copilot_inputs_fx_v1 (RUN path)
  -> invoke FX advisory pipeline
  -> put_copilot_artifact_bundle_v1
  -> answer_text from renderer

Follow-up:
  as_of_decision_ref
    -> resolve_decision_ref_to_copilot_artifacts_v1
    -> renderer intent branch (EXPLAIN/SCENARIO/LADDER)
```

QA/CI:
- QA script runs deterministic multi-stage checks and follow-ups
- GitHub Actions runs on `pull_request`, `push`, `schedule`, and `workflow_dispatch`
- Workflow seeds stable IDs and uploads JSON QA artifact

## 8. Frozen Contracts and Stable Interfaces

Major frozen contracts and stable interfaces:
- Copilot contracts:
  - `CopilotContextV1`
  - `TreasuryCopilotRequestV1`
  - `CopilotArtifactsV1`
  - `CopilotAuditV1`
  - `TreasuryCopilotResponseV1`
  - freeze tests: `tests/core/treasury/test_treasury_copilot_contract_freeze_v1.py`
- Advisory contracts:
  - `AdvisoryInputNormalizedV1` and row model in `advisory_input_contract_v1.py`
  - `AdvisoryDecisionV1` in `advisory_output_contract_v1.py`
  - service-level invariants in `tests/services/test_*_v1.py`
- Risk contracts:
  - `ScenarioSpec`, `RiskRequest`, `ScenarioGrid` and G9 artifact schemas
- Option contract surface already present:
  - `OptionContractV1` in `core/contracts/option_contract_v1.py`

Warning codes acting as contracts (Copilot):
- `fx_advisory_executed_v1`
- `read_only_followup_v1`
- `resolution_failed_v1`
- `followup_resolution_failed_v1`
- `intent_not_implemented_v1`

Frozen copilot artifact bundle schema:
- Top-level keys:
  - `advisory_decision`
  - `explainability`
  - `report_markdown`
  - `scenario_table_markdown`
  - `ladder_table_markdown`
- Guard test: `tests/core/treasury/test_copilot_artifact_bundle_schema_v1.py`

## 9. Known Architectural Gaps

The following are current observed gaps, not hypothetical:

- Ladder not connected in Copilot RUN path:
  - `invoke_fx_advisory_pipeline_v1` currently passes `ladder=None`
  - `SHOW_HEDGE_LADDER` follow-up can validly return no ladder data
- `COMPARE_POLICIES` intent registered but not implemented:
  - falls into not-implemented path with warning `intent_not_implemented_v1`
- Parser ambiguity / keyword priority limitations:
  - keyword order can classify mixed questions into unintended follow-up intent
- `scenario_table_markdown` not pre-rendered in RUN path:
  - currently set to `None` during invocation
  - follow-up scenario table often relies on fallback reconstruction from structured artifacts
- No multi-currency support in current advisory path:
  - report extraction uses primary pair from first exposure row (`_extract_primary_pair_v1`)
- No SQLite migration path:
  - `core/v2/sqlite_schema.py` enforces version `1` with hard mismatch failure, no forward migration implementation

## 10. Options Readiness

Existing reusable modules:
- Option contract: `core/contracts/option_contract_v1.py`
- Repricing harness includes options support seam: `core/risk/reprice_harness.py`
- BS SSOT pricing entry point: `core/pricing/bs_ssot_v1.py`
- Scenario/risk artifact stack already generic enough to reuse (`core/risk/*`)
- Vol provider abstraction exists (`core/vol/provider.py`, `core/vol/inmemory.py`)

Existing hook points:
- Market snapshot already includes optional vol slot:
  - `vols: Optional[VolSurfaces]` in `core/market_data/market_snapshot_payload_v0.py`
- Advisory report and explainability infrastructure can host options-oriented views (`core/services/advisory_report_v1.py`, `core/services/explainability_pack_v1.py`)

Still must be specified before options implementation:
- Vol surface resolution/validation contract from snapshot payload to pricer inputs
- Option advisory input contract and normalization rules
- Copilot artifact schema evolution/versioning strategy for options-specific outputs
- Multi-currency/multi-book advisory semantics in Copilot/advisory paths
- Persistence migration strategy beyond schema version 1

## 11. Working Rules for Future Development

Codex operating rules (aligned with `docs/architecture/codex-working-protocol.md`):
- Work from explicit task scope and one topic per PR
- Stop protocol:
  - If ambiguity, mismatch, or conflicting interpretations are found, stop and ask with minimal options
  - Do not infer architecture semantics silently
- No hidden math in interface layers:
  - API/CLI/renderer/orchestration layers must not introduce financial math not present in SSOT core modules
- Evidence block expectations for each substantive change:
  - branch evidence
  - exact file deltas
  - deterministic test evidence
  - CI/workflow evidence when relevant

Practical guardrails:
- No cross-layer leakage (`core` should not import `api`)
- Contract changes require freeze test updates and explicit versioning intent
- Closed gate behavior should not be modified without explicit reopening decision

## 12. Immediate Next Phase

**Immediate next phase:** architecture closure before options implementation.

Before options coding begins, the following specs should be closed in docs/ADRs:
- Vol snapshot-to-pricing resolution contract and invariants
- Options advisory input/output contract boundaries
- Copilot bundle extension/versioning rules for options follow-ups
- Ladder wiring decision for RUN path and expected artifact payload shape
- Parser intent disambiguation policy for mixed-language/mixed-intent prompts
- SQLite migration policy (versioning and operational compatibility)

This sequence preserves freeze discipline and prevents hidden architecture drift while expanding to options.