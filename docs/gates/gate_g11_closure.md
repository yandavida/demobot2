# Gate 11 Closure

## Gate Summary
Gate 11 is a Treasury advisory composition layer built on deterministic artifacts.
It is corporate treasury oriented: exposure input becomes risk and hedge decisions.
The gate composes existing contracts and engines without introducing new pricing behavior.
Risk core and scenario machinery remain unchanged.
Snapshot semantics remain unchanged.
G9/G10 artifact schemas remain unchanged.

## Gate 11 Closure Criteria
1. Gate 11 is closed when Advisory v1 runs end-to-end deterministically (including delta aggregate): input → adapter → G9 harness → artifacts → risk summary → hedge recommendation → output contract, identical on repeated runs.
2. Gate 11 is composition-only: no changes to pricing math, scenario engine, snapshot semantics, or any G9/G10 artifact schemas/fixtures.
3. Contracts are frozen: advisory input v1, output v1, hedge policy constraints v1, and rolling hedge ladder v1 are versioned and deterministically serialized.
4. Policy + Ladder are auditable: as_of_date is explicit (no wall-clock), bucket partitioning and ordering are stable, and target allocation is reproducible.
5. CI guards are law: certification tests enforce forbidden imports, prevent scope leakage, and run deterministic smokes for advisory + ladder flows.

## Frozen Components
- `core/services/advisory_input_contract_v1.py`
- `core/services/exposure_adapter_v1.py`
- `core/services/scenario_risk_summary_v1.py`
- `core/services/hedge_recommendation_v1.py`
- `core/services/hedge_policy_constraints_v1.py`
- `core/services/rolling_hedge_ladder_v1.py`
- `core/services/advisory_output_contract_v1.py`
- `core/services/advisory_read_model_v1.py`

## NOTE: Delta Semantics
- `delta_exposure_aggregate_domestic` is populated from ExposuresArtifact SSOT: `outputs.aggregates.delta_total_per_pct`
- This is sensitivity per % spot shock (ΔPV for a 1% move), not “per 1 unit spot”.
- This is intentionally treasury-friendly (DV01-style for FX).
- Tests for this delta must use numeric_policy tolerance:
  `DEFAULT_TOLERANCES[MetricClass.DELTA]`  (PR-9.6)
# Gate 11 Closure

## Gate Summary
Gate 11 delivers a Treasury advisory composition layer over deterministic risk artifacts.
It is corporate-treasury oriented: business FX exposures are transformed into risk and hedge decisions.
The flow composes existing deterministic components from input normalization to output envelope.
No pricing logic or risk engine internals are redefined in this gate.
No scenario generation semantics are altered.
No artifact schema contracts are modified.

## Gate 11 Closure Criteria
1. Gate 11 is closed when Advisory v1 runs end-to-end deterministically (including delta aggregate): input -> adapter -> G9 harness -> artifacts -> risk summary -> hedge recommendation -> output contract, identical on repeated runs.
2. Gate 11 is composition-only: no changes to pricing math, scenario engine, snapshot semantics, or any G9/G10 artifact schemas/fixtures.
3. Contracts are frozen: advisory input v1, output v1, hedge policy constraints v1, and rolling hedge ladder v1 are versioned and deterministically serialized.
4. Policy + Ladder are auditable: as_of_date is explicit (no wall-clock), bucket partitioning and ordering are stable, and target allocation is reproducible.
5. CI guards are law: certification tests enforce forbidden imports, prevent scope leakage, and run deterministic smokes for advisory + ladder flows.

## Frozen Components
- `core/services/advisory_input_contract_v1.py`
- `core/services/exposure_adapter_v1.py`
- `core/services/scenario_risk_summary_v1.py`
- `core/services/hedge_recommendation_v1.py`
- `core/services/hedge_policy_constraints_v1.py`
- `core/services/rolling_hedge_ladder_v1.py`
- `core/services/advisory_output_contract_v1.py`
- `core/services/advisory_read_model_v1.py`

## NOTE: Delta Semantics
- `delta_exposure_aggregate_domestic` is populated from ExposuresArtifact SSOT: `outputs.aggregates.delta_total_per_pct`.
- This is sensitivity per % spot shock (Delta PV for a 1% move), not "per 1 unit spot".
- This is intentionally treasury-friendly (DV01-style for FX).
- Tests for this delta must use numeric policy tolerance: `DEFAULT_TOLERANCES[MetricClass.DELTA]` (PR-9.6).
