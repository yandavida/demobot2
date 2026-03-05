# Gate 11 Closure

## Gate Summary
Gate 11 delivers a Treasury advisory composition layer over deterministic risk artifacts.
It is corporate-treasury oriented: business FX exposures are transformed into risk and hedge decisions.
The flow composes existing deterministic components from input normalization to output envelope.
No pricing logic or risk engine internals are redefined in this gate.
No scenario generation semantics are altered.
No artifact schema contracts are modified.

## Gate 11 Closure Criteria (5 lines)
1. Advisory IO is frozen: AdvisoryInputContractV1 + AdvisoryDecisionV1 are deterministic and test-guarded.
2. Risk is SSOT: scenario risk, exposures, and surface come only from G9 artifacts; no math duplication in app layer.
3. Hedge outputs are executable: trade tickets + policy constraints + rolling hedge ladder are deterministic and bucket-consistent (Sigma bucket additional = global additional).
4. Advisory Report v1 is shipped: render_advisory_report_markdown_v1 exists, deterministic, and contains the required headings + executive takeaway + ticket summary.
5. CI is the contract: Gate-11 certification guards pass and protect G9/G10 schemas/fixtures from drift.

## Frozen Components
- `core/services/advisory_input_contract_v1.py`
- `core/services/exposure_adapter_v1.py`
- `core/services/scenario_risk_summary_v1.py`
- `core/services/hedge_recommendation_v1.py`
- `core/services/hedge_policy_constraints_v1.py`
- `core/services/rolling_hedge_ladder_v1.py`
- `core/services/advisory_output_contract_v1.py`
- `core/services/advisory_read_model_v1.py`
- `core/services/advisory_report_v1.py`

## NOTE: Units And Semantics
- Delta aggregate is per 1% spot shock (not per unit spot).
- Post-policy ratio is executable and must match ladder/ticket outputs.
- Target worst loss total (domestic) in report is sum of ladder bucket targets (no new risk math).
